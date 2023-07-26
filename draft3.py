import asyncio
from datetime import date, timedelta
from textwrap import indent

from redis import Redis

from config import profile
from kbgpt.api.aigc.report_models import Report, Type
from kbgpt.lib.exec.exec import *
from kbgpt.lib.templates.rendering.models import RedisTemplateProvider, TemplateRepo

report = Node(
    engine=ReportEngineMod(
        type="report_engine",
        name="report_daily",
        render_config={"coverBreakSec": 1.7, "pageBreakSec": 1, "listingBreakSec": 1},
    ),
    in_keys=["dt", "req", "name"],
)

polish = Node(
    engine=SimpleEngineMod(type="simple_engine", name="report_polish"),
    in_keys=["content"],
)

adjust = Node(
    engine=SimpleEngineMod(
        type="simple_engine", name="report.daily.adjust_space_and_breaks"
    ),
    in_keys=["content"],
)

r_map = Node(
    engine=MapperEngineMod(type="mapper_engine", mapping={"content": "content"})
)

p_map = Node(
    engine=MapperEngineMod(type="mapper_engine", mapping={"content": "content"})
)

a_map = Node(
    engine=MapperEngineMod(type="mapper_engine", mapping={"content": "content"})
)

pipe = [report, r_map, adjust, a_map, polish, p_map]

serial = SerialPipe(nodes=pipe)

print(serial.json(indent=4))

redis = Redis.from_url(profile.vector_store.redis_url)
temp_repo = TemplateRepo(RedisTemplateProvider(redis))

factory = engine_factory.EngineFactory(temp_repo)

asyncio.run(
    serial.aexec(
        engine_factory=factory,
        seed={
            "req": Report(
                type=Type.WEEKLY, date=date.fromisoformat("2023-07-21"), polish=True
            ),
            "name": "report.weekly.jinja",
            "showListings": False,
        },
    )
)
