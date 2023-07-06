from sanic import Blueprint

from .sentiment import SENTIMENT

SENSHIP = Blueprint.group(
    SENTIMENT, version_prefix="/api/v", url_prefix="senship", version=1
)
