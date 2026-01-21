import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.core.ctx_vars import request_id_ctx_var
from src.core.logger import logger


class InfoRequestMiddleWare(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_ctx_var.set(request_id)
        logger.info("Start request")
        response = await call_next(request)
        logger.info("End request")
        return response
