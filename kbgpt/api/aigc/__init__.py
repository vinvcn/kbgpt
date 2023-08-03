from sanic import Blueprint

from .agg import AGG
from .comment import COMMENT
from .qa import QA
from .report import RP

AIGC = Blueprint.group(
    AGG, COMMENT, QA, RP, version_prefix="/api/v", url_prefix="aigc", version=1
)
