from fastapi import HTTPException
from starlette.responses import JSONResponse

from . import media


class UploadBodyLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope["path"].endswith("/upload"):
            return await self.app(scope, receive, send)
        limit = media.MAX_UPLOAD_BYTES + 1024 * 1024
        headers = dict(scope.get("headers", []))
        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            return await JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)(scope, receive, send)
        if declared > limit:
            return await JSONResponse({"detail": "Upload request too large"}, status_code=413)(scope, receive, send)
        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > limit:
                raise HTTPException(413, "Upload request too large")
            return message

        await self.app(scope, limited_receive, send)
