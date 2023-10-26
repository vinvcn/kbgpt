import enum

from pydantic import BaseModel, Field

from kbgpt.lib.exec.clients.redis import REDIS_CLIENT
from kbgpt.lib.exec.engines.configs.models import PersistLevel
