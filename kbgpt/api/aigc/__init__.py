from sanic import Blueprint

from .comment import COMMENT
from .qa import QA

AIGC = Blueprint.group(
    COMMENT, QA, version_prefix="/api/v", url_prefix="aigc", version=1
)
