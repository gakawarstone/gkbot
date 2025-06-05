from services.http import HttpService


class LitterboxUploader:
    host_url = "https://litterbox.catbox.moe/resources/internals/api.php"

    @classmethod
    async def upload_with_path(cls, path: str) -> str:
        file = open(path, "rb")
        try:
            data = {
                "reqtype": "fileupload",
                "fileToUpload": file,
                "time": "1h",
            }
            response = await HttpService.post(cls.host_url, body=data)
        finally:
            file.close()

        return response.decode("utf-8")
