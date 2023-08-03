from sanic import Blueprint

from .admin import TASK

ADMIN = Blueprint.group(TASK, version_prefix="/api/v", url_prefix="admin", version=1)
