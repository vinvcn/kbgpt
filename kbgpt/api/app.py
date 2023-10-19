"""
web app
"""
import json

from jinja2 import FileSystemLoader
from redis import Redis
from sanic import Sanic
from sanic.server.protocols.websocket_protocol import WebSocketProtocol
from sanic_ext import Extend
from sanic_jinja2 import SanicJinja2

import kbgpt.api.libs.resources
from config import profile
from kbgpt.api.aigc.report import DailyReport, WeeklyReport
from kbgpt.api.libs.resources import ResourceMgr
from kbgpt.fe.fe import FE
from kbgpt.lib.db.cache_store import RedisCacheStoreStrategy
from kbgpt.lib.db.mysql import Crud
from kbgpt.lib.exec.clients.redis import REDIS_CLIENT
from kbgpt.lib.exec.qa.utils import get_cache_index_from_graph
from kbgpt.lib.logging.mysql_emitter import MySqlEmitter
from kbgpt.lib.tasks.manager import TaskManager
from kbgpt.lib.templates.rendering.models import RedisTemplateProvider, TemplateRepo
from kbgpt.svc.aigc.kb import UpdateKBFromDB
from kbgpt.svc.aigc.qa.file_services import WarmupTask
from kbgpt.svc.aigc.qa.qa_graph import QA_GRAPH
from kbgpt.svc.aigc.qa.qa_graph_fetch_context import CONTEXT_GRAPH
from kbgpt.svc.aigc.qa.qa_graph_wizout_tailor import RECOMMEND_GRAPH
from kbgpt.svc.aigc.qa.qa_top import QA_TOP_GRAPH

from .admin import ADMIN
from .aigc import AIGC
from .legacy.apis import LEGACY
from .senti import SENSHIP
from .tune import TUNE

app = Sanic(
    profile.sanic.app_name,
)
app.config.RESPONSE_TIMEOUT = profile.sanic.response_timeout
app.config.CORS_ORIGINS = (
    "http://foobar.com,http://localhost:8082,http://10.2.0.111:8082"
)
Extend(app)
app.static("/", "kbgpt/fe/dist")

app.blueprint(AIGC)
app.blueprint(ADMIN)
app.blueprint(SENSHIP)
app.blueprint(LEGACY)
app.blueprint(FE)
app.blueprint(TUNE)

app.ctx.jinja = SanicJinja2(
    app=app,
    loader=FileSystemLoader(searchpath=["kbgpt/fe/dist"]),
    enable_async=True,
)

if profile.openai.proxied:
    import openai

    openai.api_base = str(profile.openai.api_base_url)
    openai.proxy = str(profile.openai.proxy_url)


@app.before_server_start
async def setup_resources(sanic_app: Sanic, loop):
    """
    Setup all resources to be used later on.
    """

    crud = Crud(profile.db_url)
    sql_emitter = MySqlEmitter(crud)
    mgr = ResourceMgr(sanic_app)
    mgr.add(crud)
    mgr.add(sql_emitter)

    task_manager = TaskManager(app=app, crud=crud)
    task_manager.register_task_name_handle(DailyReport, DailyReport.__name__)
    task_manager.register_task_name_handle(WeeklyReport, WeeklyReport.__name__)
    task_manager.register_task_name_handle(WarmupTask, WarmupTask.__name__)
    task_manager.register_task_name_handle(UpdateKBFromDB, UpdateKBFromDB.__name__)

    mgr.add(task_manager)

    await mgr.init_all()
    kbgpt.api.libs.resources.MGR = mgr
    sanic_app.ctx.res = mgr

    sanic_app.ctx.redicache = RedisCacheStoreStrategy()
    redis = Redis.from_url(profile.vector_store.redis_url)
    sanic_app.ctx.temp_repo = TemplateRepo(RedisTemplateProvider(redis))
    sanic_app.add_task(sql_emitter.aloop_drain(), name="sql_emitter_drain_loop")
    sanic_app.add_task(task_manager.schedule, name="task_scheduler_loop")

    all_caches = get_cache_index_from_graph(QA_TOP_GRAPH)
    cache_indexes = set([cac.index_name for cac in all_caches])
    sanic_app.ctx.cache = {"indexes": cache_indexes}
    REDIS_CLIENT.init_all_indexes(cache_indexes)


@app.after_server_stop
async def cleanup_resources(sanic_app: Sanic):
    """
    Clean up resources setup earlier.
    """
    mgr: ResourceMgr = sanic_app.ctx.res
    await mgr.destroy_all()


def run():
    """
    run the web app
    """
    app.run(
        host=profile.sanic.ip,
        port=profile.sanic.port,
        debug=profile.sanic.debug,
        workers=profile.sanic.workers,
        protocol=WebSocketProtocol,
    )
