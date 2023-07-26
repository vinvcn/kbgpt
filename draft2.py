import asyncio

from aiokafka import AIOKafkaConsumer
from aiokafka import AIOKafkaProducer


# servers = [ "b-1.bullsmartfat03.7llksk.c3.kafka.ap-southeast-1.amazonaws.com:9092", "b-2.bullsmartfat03.7llksk.c3.kafka.ap-southeast-1.amazonaws.com:9092" ]
servers = ["18.139.228.114:9092","18.139.228.114:9093"]
daily_topic = "mb-market-aigc-daily-report"


producer = AIOKafkaProducer(bootstrap_servers=servers)

await producer.start()

# for i in range(10):
await producer.send_and_wait(daily_topic, b"Super message")

await producer.stop()

# consumer = AIOKafkaConsumer(
#     daily_topic,
#     bootstrap_servers=servers,
#     request_timeout_ms=1000,
# )

consumer = AIOKafkaConsumer(
    daily_topic,
    bootstrap_servers=servers,
    auto_offset_reset='earliest',
    enable_auto_commit=False)

await consumer.start()
# we want to consume 10 messages from "foobar" topic
# and commit after that
# for _ in range(10):
msg = await consumer.getone()
print(msg)

await consumer.start()
# await consumer.getone()

async for msg in consumer:
    print(msg)

await consumer.stop()


async def consume():
d_csmr = AIOKafkaConsumer(
    daily_topic,
    bootstrap_servers=servers
)
d_csmr = AIOKafkaConsumer(
    "mb-market-aigc-daily-report",
    bootstrap_servers="b-1.bullsmartfat03.7llksk.c3.kafka.ap-southeast-1.amazonaws.com:9092"
)
    w_csmr = AIOKafkaConsumer(
        "mb-market-aigc-weekly-report",
        bootstrap_servers=[
            "b-1.bullsmartfat03.7llksk.c3.kafka.ap-southeast-1.amazonaws.com:9092",
            "b-2.bullsmartfat03.7llksk.c3.kafka.ap-southeast-1.amazonaws.com:9092"
        ]
    ) 
    # Get cluster layout and join group `my-group`
    try:
        # Consume messages
        async for msg in consumer:
            print(
                "consumed: ",
                msg.topic,
                msg.partition,
                msg.offset,
                msg.key,
                msg.value,
                msg.timestamp,
            )
    finally:
        # Will leave consumer group; perform autocommit if enabled.
        await consumer.stop()


asyncio.run(consume())
