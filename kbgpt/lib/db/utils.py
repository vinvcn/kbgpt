import logging

from redis.client import Redis as RedisType


def check_index_exists(client: RedisType, index_name: str) -> bool:
    """Check if Redis index exists."""
    try:
        client.ft(index_name).info()
    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.exception(e)
        logging.error("fetching index information failed")
        return False
    logging.info("Index already exists")
    return True
