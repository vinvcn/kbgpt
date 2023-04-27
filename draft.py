import asyncio
import uuid
from os import getcwd, mkdir, path

import aioredis
from aiofiles import open as aopen
from aiofiles import tempfile
from aioredis.client import Redis


async def get_keys_and_values(
    redis: Redis, cursor: int, batch_size: int, match: str
):
    # Use SCAN command to get next set of keys matching pattern (in this case, all keys)
    cursor, keys = await redis.scan(
        cursor=cursor, match=match, count=batch_size
    )

    # Use MGET command to get corresponding values for each key
    values = await redis.mget(keys=keys)

    # Return a tuple of (keys, values) for this batch
    return (keys, values), cursor


async def scan_iter(redis: Redis, match: str):
    cursor = None
    batch_size = 10000
    rdir = path.join(getcwd(), ".redis")
    if not path.exists(rdir):
        mkdir(rdir)
    fpath = path.join(rdir, f"{str(uuid.uuid4())}.txt")
    fio = open(fpath, "wb")

    while cursor != 0:
        cursor, keys = await redis.scan(
            cursor=cursor or 0, match=match, count=batch_size
        )
        if keys:
            for k in keys:
                content = await redis.hmget(k, "content")
                for c in content:
                    fio.write(c)
                    fio.write(b"\n")
                    yield content


async def main():
    # Connect to Redis instance using aioredis
    redis = aioredis.from_url("redis://localhost:6379")

    # Set initial cursor value to 0 and batch size to 10
    cursor = 0
    batch_size = 10

    # Initialize empty list to store retrieved keys and values
    results = []

    match = "doc:cache-bullsmart-customer-services:*"

    # Loop through Redis keys using SCAN command and get batches of 10 keys and values at a time
    async for item in scan_iter(redis=redis, match=match):
        print(item)

    # Close Redis connection
    await redis.close()

    # Print retrieved keys and values
    print(results)


# Run the main async function
asyncio.run(main())
