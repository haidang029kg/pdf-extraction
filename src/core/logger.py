import logging
import logging.config
import os

from .ctx_vars import request_id_ctx_var
from .settings import settings


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_ctx_var.get()
        return True


request_id_filter = RequestIdFilter()

os.makedirs(settings.LOG_DIR, exist_ok=True)
os.makedirs(settings.LOG_DIR / "ocr", exist_ok=True)

logging.config.fileConfig(
    settings.ROOT_DIR / "logging.ini",
    disable_existing_loggers=False,
)

logger = logging.getLogger()
ocr_logger = logging.getLogger("ocr")

for _handler in [*logger.handlers, *ocr_logger.handlers]:
    _handler.addFilter(request_id_filter)
