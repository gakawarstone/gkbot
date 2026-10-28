import asyncio
import socket
import threading
from pathlib import Path
from typing import Any, Literal
from unittest.mock import AsyncMock

import pytest
from gallery_dl.extractor.tiktok import TiktokExtractor, TiktokPostExtractor
from gallery_dl.job import DataJob
from requests import Response

from services.gallery_dl import (
    GalleryDlExtractionError,
    GalleryDlService,
    GalleryDlSlideshowInfo,
)
from services.http import HttpService
from services.tiktok.extractor import _EXTRACTORS, TikTokInfoExtractor
from services.tiktok.extractor._base import BaseExtractor
from services.tiktok.extractor.exceptions import SourceInfoExtractFailed

URL = "https://www.tiktok.com/@offline/video/1"
IMAGES = ["https://example.invalid/first.jpg", "https://example.invalid/second.jpg"]


@pytest.fixture
def offline_slideshow(monkeypatch: pytest.MonkeyPatch) -> bytes:
    fixture = Path(__file__).parents[1] / "fixtures/gallery_dl/tiktok-slideshow.json"
    html = (
        '<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">'
        + fixture.read_text()
        + "</script>"
    ).encode()

    def request(extractor: TiktokExtractor, url: str) -> Response:
        response = Response()
        response.url = url
        response.status_code = 200
        response._content = html
        return response

    def forbid_connect(*args: Any, **kwargs: Any) -> None:
        pytest.fail("Offline gallery-dl test attempted a network connection")

    monkeypatch.setattr(TiktokExtractor, "request", request)
    monkeypatch.setattr(socket.socket, "connect", forbid_connect)
    return html


async def test_real_data_job_lifecycle_and_tiktok_fallback(
    offline_slideshow: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    loop_thread = threading.get_ident()
    phases: list[tuple[str, int]] = []
    attempts: list[BaseExtractor] = []

    class ObservedDataJob(DataJob):
        def __init__(self, url: str, *, file: None) -> None:
            phases.append(("construct", threading.get_ident()))
            super().__init__(url, file=file)

        def run(self) -> Literal[0]:
            phases.append(("run", threading.get_ident()))
            return super().run()

        def __getattribute__(self, name: str) -> Any:
            if name in ("data", "exception"):
                phases.append((name, threading.get_ident()))
            return super().__getattribute__(name)

    async def fail(source: BaseExtractor, url: str) -> None:
        attempts.append(source)
        raise SourceInfoExtractFailed(source)

    monkeypatch.setattr("services.gallery_dl.DataJob", ObservedDataJob)
    for source in _EXTRACTORS[:2]:
        monkeypatch.setattr(type(source), "get_video_info", fail)
    redirect = AsyncMock(return_value=URL)
    monkeypatch.setattr(HttpService, "get_redirected_url", redirect)

    result = await TikTokInfoExtractor.get_video_info(URL)

    assert attempts == _EXTRACTORS[:2]
    redirect.assert_awaited_once_with(URL)
    assert result.images_urls == IMAGES
    assert result.music_url == "https://example.invalid/music.mp3"
    assert (result.width, result.height, result.duration) == (720, 1080, None)
    assert result.video_url is None and result.video_input_file is None
    assert {phase for phase, _ in phases} == {"construct", "run", "data", "exception"}
    assert len({thread for _, thread in phases}) == 1
    assert all(thread != loop_thread for _, thread in phases)


@pytest.mark.parametrize("failure", ["status", "recorded", "empty", "unsupported"])
async def test_real_data_job_failures_are_extraction_errors(
    offline_slideshow: bytes, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    if failure == "status":
        run = DataJob.run

        def failed_status(job: DataJob) -> int:
            run(job)
            return 1

        monkeypatch.setattr(DataJob, "run", failed_status)
    elif failure == "recorded":
        # DataJob.run records dispatch errors in job.exception and returns zero.
        def fail_url(job: DataJob, url: str, metadata: dict[str, Any]) -> None:
            raise ValueError("Generated dispatch failure")

        monkeypatch.setattr(DataJob, "handle_url", fail_url)
    elif failure == "empty":
        monkeypatch.setattr(TiktokPostExtractor, "posts", lambda self: {})

    url = "https://example.invalid/unsupported" if failure == "unsupported" else URL
    with pytest.raises(GalleryDlExtractionError) as raised:
        await GalleryDlService.extract_slideshow_info(url)
    if failure in ("status", "recorded"):
        assert isinstance(raised.value.__cause__, ValueError)
        assert str(raised.value.__cause__) == "gallery-dl failed to extract data"


@pytest.mark.parametrize("fail", [False, True])
async def test_cancellation_waits_for_real_job_before_caller_cleanup(
    offline_slideshow: bytes,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    fail: bool,
) -> None:
    started = threading.Event()
    release = threading.Event()
    finished = threading.Event()
    request = TiktokExtractor.request
    resource = tmp_path / "caller-owned"
    resource.mkdir()

    def held_request(extractor: TiktokExtractor, url: str) -> Response:
        started.set()
        assert release.wait(timeout=5)
        assert resource.is_dir()
        (resource / "finished").write_text("complete")
        return request(extractor, url)

    class ObservedDataJob(DataJob):
        def run(self) -> Literal[0]:
            try:
                status = super().run()
                if fail:
                    self.exception = ValueError("Generated job failure")
                return status
            finally:
                finished.set()

    monkeypatch.setattr(TiktokExtractor, "request", held_request)
    monkeypatch.setattr("services.gallery_dl.DataJob", ObservedDataJob)

    async def caller() -> GalleryDlSlideshowInfo:
        try:
            return await GalleryDlService.extract_slideshow_info(URL)
        finally:
            assert finished.is_set()
            (resource / "finished").unlink()
            resource.rmdir()

    task = asyncio.create_task(caller())
    try:
        assert await asyncio.to_thread(started.wait, 5)
        for _ in range(2):
            task.cancel()
            await asyncio.sleep(0)
            assert not task.done()
            assert resource.is_dir()
        # The held worker does not prevent another callback from running.
        callback = AsyncMock()
        await asyncio.create_task(callback())
        callback.assert_awaited_once()
    finally:
        release.set()
    # Match wait_for_completion: a worker failure takes precedence over cancellation.
    expected_error = GalleryDlExtractionError if fail else asyncio.CancelledError
    with pytest.raises(expected_error):
        await task
    assert not resource.exists()
