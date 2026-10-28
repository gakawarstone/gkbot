# TikTok: YoutubeDL lifecycle и готовность удаления

28 октября 2026. База `2db43ed99af695c841ed7c29194df88da8d42225`, ветка `fix/tiktok-feed-loop-latency`. Анализ и измерения выполнены локально; Telegram sends и удаления production feed не выполнялись. Публикация отдельного PR разрешена пользователем после подготовки и проверки diff.

## Вывод и решение

Первый extractor TikTok вызывает `YtdlpDownloader._get_info`, затем `_download_file`. Оба метода создавали `yt_dlp.YoutubeDL` и выходили из его context manager в event loop. Только `extract_info` и `download` выполнялись в executor. Поэтому async download сам по себе не защищал callback от синхронного конструктора.

На настоящем YoutubeDL 2026.8.19, с заменой только сетевой extraction/download части, тёплый `_get_info` занимал около 21 мс. Диагностический cProfile показал основную работу в `YoutubeDL.__init__ -> add_default_info_extractors -> orderedSet_from_options`, с регистрацией 1744 extractors. Это измерение установленного кода, без сети, а не искусственный sleep вместо конструктора.

Исправление переносит весь `construct -> enter -> extract/download -> exit` одним вызовом в существующий executor. Выбор имени файла и `os.path.exists` после download тоже выполняются там. Результатом остаются metadata или путь, `FSInputFile` создаётся после завершения job. Ветка удалённого YouTube worker сохраняется.

`wait_for_completion` задерживает распространение cancellation до завершения job и закрытия YoutubeDL. Затем context manager может очистить каталог или поставить отложенную очистку. Следующая локальная конвертация TikTok через ffmpeg защищена тем же ожиданием, чтобы cleanup не удалял файлы под работающим writer. Helper уже существовал в проекте, новой общей зависимости нет.

Это устраняет доказанную блокировку на время конструктора в loop, но поток всё ещё конкурирует за GIL. В контроле после исправления задержка удаления остаётся около 5,3 мс. Работа не устанавливает причину конкретного production-фриза и не доказывает исчезновение всех задержек фида.

## Итоговые замеры

Источник чисел ниже `results-before-cold.json`, снятый под общим measurement lock. Каждый warm сценарий повторён 10 раз. Все времена в миллисекундах относительно одной readiness deadline, если не указано иное. Указаны median и максимум серии, не production p95.

- Idle: dispatch 0,140 / 0,171; вызов delete 0,146 / 0,186.
- `_get_info` до: dispatch 17,219 / 18,438; delete 17,225 / 18,447. После: dispatch 5,242 / 5,428; delete 5,249 / 5,435.
- `_download_file` до: dispatch 17,999 / 20,235; delete 18,006 / 20,244. После: dispatch 5,239 / 5,266; delete 5,245 / 5,271.
- Настоящий TikTok view flow до границы отправки до: dispatch 18,523 / 19,561; delete 18,528 / 19,580. После: dispatch 5,360 / 5,425; delete 5,366 / 5,433.
- Wall самого view flow: до 43,776 / 47,706; после 42,417 / 43,791. Ускорение появления следующего поста не является критерием этого исправления.

Отдельный fresh process в `results-after-cold.json` повторил warm контроль. Delete view flow до 17,485 / 20,600, после 5,359 / 5,476. В каждой серии первая измеренная инициализация отмечена `cold`, до прогрева конструктора. Это по одному наблюдению, статистику cold latency они не задают. В первом процессе cold info до: wall 35,878, delete 31,921. Во втором процессе cold info после: wall 32,992, delete 5,499. Package imports до старта probe исключены, поэтому это не измерение всего старта приложения.

Контроль timer: синхронный sleep 20 мс дал median delete lateness 16,170 мс при median фактическом readiness offset 3,914 мс от начала операции. Вторая серия дала 16,158 мс. Это калибровка планирования таймера, не модель скорости источника.

## Что проверено по всему flow

- `_process_tiktok_item -> TikTokService.get_video -> TikTokInfoExtractor -> YtDlp -> YtdlpDownloader -> FSInputFile -> _send_video_item` выполняется настоящим кодом в view-flow probe. Только extraction/download сети, ffmpeg conversion, scheduler DB и граница Telegram send заменены локальными stubs. Metadata полные, поэтому ffprobe в этом сценарии не запускается.
- Extractors идут последовательно до первого успеха: YtDlp, api.douyin.wtf, GalleryDl, TikWm, TTDownloader, второй API, Snaptik, Mdown, Tikdown. Успешный первый extractor в probe доказывает достижимость YoutubeDL без предварительных отказов других источников. Частота отдельных fallback в production не измерена.
- API/TikWm/Tikdown используют aiohttp. Их async network wait отличается от CPU stall. Синхронное JSON/regex преобразование остаётся, но сохранённых больших ответов, доказывающих существенный вклад, здесь нет.
- TTDownloader и Mdown выполняют requests и их разбор через `async_wrap`. Вызов sync requests в loop на этих путях не обнаружен. CPU/GIL конкуренция потоков возможна, но отдельно не измерялась.
- GalleryDl создаёт `DataJob` в loop. Эта независимая находка передана отдельному top-level `mcp:0c4cf8f7-e723-43c3-9113-5c2fa6c63688`. Её предварительные данные сохранены вне этого PR; gallery code и gallery серии в итоговый harness не входят.
- Snaptik выполняет decoder и `literal_eval` в loop. Масштаб проверен только на generated responses; отдельное решение и границы вывода приведены ниже.
- Обычная запись TikTok-видео через `to_thread`, slideshow path handoff и `_TikTokCacheDir` cleanup уже были исправлены до этой ветки. Повторно приписывать им исторические 83 MiB результаты нельзя.
- Metadata ffprobe и ffmpeg запускаются через executor; общий ffmpeg semaphore ожидается асинхронно. Синхронные mkdir в CacheDir и copy одного/двух подготовленных JPEG остаются. Значимой задержки на актуальном реалистичном входе для них здесь не доказано. Отложенная очистка обычного CacheDir из yt-dlp тоже остаётся синхронной; это отдельный scheduled путь, не текущая YoutubeDL job.
- Установленный `FSInputFile.read` использует `aiofiles.open/read`. Новая реализация не читает весь MP4 в loop перед отправкой. Настоящая отправка Telegram не выполнялась. Существующие TikTok tests проверяют, что файл читается после возврата сервиса и сохраняется во время upload.

## Отдельное решение по Snaptik

Проверен настоящий `Snaptik.get_video_info` с generated valid encoded response и локальными HTTP stubs. Для 1000/10000/100000 filler characters decoded HTML median delete lateness составила 0,209 / 4,134 / 75,386 мс в первой итоговой серии. Поэтому механизм блокировки и рост задержки с размером подтверждены на искусственных входах.

Реальный масштаб не установлен: сохранённых production-ответов Snaptik в этом исследовании нет, распределение их размеров и частота fallback не измерены. Достижимость седьмого extractor подтверждена чтением последовательной цепочки после отказов первых шести; controlled проход всей цепочки с этими отказами не выполнялся. Отдельный Snaptik probe не доказывает, что такой ответ участвовал в пользовательском фризе.

Snaptik не включён в YoutubeDL PR, поскольку для него нет доказательства существенной задержки на реалистичном входе или runtime trace. Это открытая гипотеза, а не закрытая или опровергнутая причина. Для обоснования отдельного исправления нужны сохранённый реалистичный ответ либо trace с достижением Snaptik, размером ответа и задержкой decode. Синтетические 100000 characters сами по себе такого обоснования не дают.

## Polling slots и сетевое ожидание

Лимит polling в проекте равен 10. В отдельной модели настоящие `Dispatcher._process_with_semaphore` и acquire-before-launch, как в polling, обслуживают десять TikTokService tasks. Extraction info заменена маленьким объектом, HTTP ждёт управляемый async event. Это модель admission, не Telegram polling end-to-end.

Callback становится ready, пока заняты все десять слотов. После заданного async sleep 50 мс задачи освобождаются. В первой серии timer получает loop через 0,144 мс после deadline, handler входит через 47,975 мс, delete вызывается через 47,983 мс. Во второй серии соответственно 0,133 / 46,704 / 46,708 мс. Значит ожидание всех слотов способно задерживать handler при свободном loop. Один медленный TikTok download сам по себе не занимает все десять слотов. Этот PR не меняет admission или callbacks.py.

## Методика и ограничения

Python 3.13.11, uvloop 0.22.1, aiogram 3.31.0, yt-dlp 2026.8.19. Входы YoutubeDL полностью generated: URL example TikTok, маленькая metadata, маленький файл stub. Конструктор, context entry/exit, выбор output path и цепочка сервиса настоящие. Для baseline harness читает downloader из указанного git revision через read-only `git show`, загружая его отдельным модулем.

Перед каждым probe loop проходит sleep 10 мс. Затем ставится timer на +5 мс, после постановки выполняется `await sleep(1ms)`, чтобы uvloop armed timer до входа в синхронную baseline операцию. `actual_ready_offset_ms` сохраняет разницу deadline и настоящего старта операции. Все итоговые offsets положительны: первая серия 3,868–4,976 мс, вторая 3,871–3,959 мс. Для before и after используется одинаковая постановка deadline. В raw отдельно сохранены timer dispatch, handler dispatch и вызов delete.

Callback вызывает настоящий `ItemEventHandler._handle_event` с настоящими моделями CallbackQuery/Message. Credentials заранее готовы, Telegram delete и feed API delete заменены stubs. Измеряется готовность к вызову delete API, а не доставка нажатия из Telegram или момент исчезновения сообщения в клиенте.

Реальной сети нет: socket.connect запрещён, yt-dlp extract/download заменены. Fake configs.env исключает чтение deployment .env. Все файлы создаются в TemporaryDirectory; scheduler DB заменена AsyncMock. Cleanup тестовой директории вне timed section. Финальные серии не пересекались с собственными tests/type checks и сериализованы общим flock. Фоновая системная нагрузка не исключалась. Порядок warm before/after фиксирован, это небольшая диагностическая серия.

Предварительные цифры без measurement lock или без await после постановки timer в итог не включены. Они сохранены в `/home/gws/.cache/gkbot-feed-loop-audit/20261028/tiktok/` с префиксом `preliminary`. Старые filesystem benchmarks от 21–22 октября использованы только как история уже выполненных исправлений; их входы и числа не являются текущими latency measurements.

## Проверки и воспроизведение

```bash
make test PYTHON=/home/gws/.t3/worktrees/gkbot/feat-feed-item-summaries/.venv/bin/python FILE='bot/tests/services/test_ytdlp_lifecycle.py bot/tests/services/test_tiktok_service.py bot/tests/services/test_snaptik_decoder.py bot/tests/services/test_ffmpeg.py'
```

52 passed, две существующие Tortoise DeprecationWarning. 19 новых tests проверяют delete во время construct/enter/operation/exit, единый поток lifecycle, повторную cancellation с immediate/delayed cleanup, ffmpeg writer cancellation, context close при DownloadError, output path после postprocessor и конвертации, сохранение YouTube worker ветки.

Родитель дополнительно выполнил полный `make test` в этом worktree с той же shared venv под общим measurement flock: 180 passed, 13 skipped, 5 existing warnings, 4,71 с. Отдельный общий integration run четырёх независимых исправлений во временном `/tmp` snapshot завершился с 202 passed, 13 skipped, 5 existing warnings, 11,60 с. Исходные checkout и branches не смешивались. Оба результата получены от родителя; повторные test runs для обновления документации не выполнялись.

Mypy с `--follow-imports=silent` и pyright с указанным shared Python проходят для production file и новых tests. Ruff новых tests/harness, typos и formatting проходят. `make lint FILE='bot/services/ytdlp/downloader.py bot/tests/services/test_ytdlp_lifecycle.py'` останавливается на существующем TRY004 у `ValueError("yt-dlp returned invalid metadata")`; та же ошибка воспроизводится на baseline из HEAD. Это поведение исключения не менялось. `git diff --check` проходит.

Оба следующих запуска выполняются из корня worktree, последовательно, без одновременных tests. В JSON сохранены raw samples, версии и SHA-256 source/harness.

```bash
flock /tmp/gkbot-feed-loop-audit-20261021/measurement.lock env PYTHONPATH=bot /home/gws/.t3/worktrees/gkbot/feat-feed-item-summaries/.venv/bin/python benchmarks/feed_loop/tiktok/lifecycle.py --cold-mode before --repetitions 10 --output benchmarks/feed_loop/tiktok/results-before-cold.json
flock /tmp/gkbot-feed-loop-audit-20261021/measurement.lock env PYTHONPATH=bot /home/gws/.t3/worktrees/gkbot/feat-feed-item-summaries/.venv/bin/python benchmarks/feed_loop/tiktok/lifecycle.py --cold-mode after --repetitions 10 --output benchmarks/feed_loop/tiktok/results-after-cold.json
```
