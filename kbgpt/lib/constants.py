"""
Constants used in the project.
"""
from enum import Enum

CACHE_STATUS_KEY = "redis_cache_status"
INDEX_VERSION_KEY = "customer_service_index_version"
REDIS_DOCUMENT_LOCK_NAME = "cache-index-lock"


class CacheStatus(Enum):
    """
    Cache status
    """

    VALID = "valid"
    INVALID = "invalid"
