from sanic import Blueprint

from .rating import RATE

TUNE = Blueprint.group(RATE, version_prefix="/api/v", url_prefix="tune", version=1)
