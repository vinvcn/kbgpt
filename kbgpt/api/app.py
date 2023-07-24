"""
web app
"""
from redis import Redis
from sanic import Sanic
from sanic.server.protocols.websocket_protocol import WebSocketProtocol

from config import profile
from kbgpt.api.aigc.report import TestTask
from kbgpt.api.libs.resources import ResourceMgr
from kbgpt.lib.db.cache_store import RedisCacheStoreStrategy
from kbgpt.lib.db.mysql import Crud
from kbgpt.lib.logging.mysql_emitter import MySqlEmitter
from kbgpt.lib.tasks.manager import TaskManager
from kbgpt.lib.templates.rendering.models import (
    MySqlTemplateProvider,
    RedisTemplateProvider,
    TemplateRepo,
)

from .admin import ADMIN
from .aigc import AIGC
from .legacy.apis import LEGACY
from .senti import SENSHIP

app = Sanic(profile.sanic.app_name)


app.blueprint(AIGC)
app.blueprint(ADMIN)
app.blueprint(SENSHIP)
app.blueprint(LEGACY)


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
    task_manager.register_task_name_handle(TestTask)

    mgr.add(task_manager)

    await mgr.init_all()
    sanic_app.ctx.res = mgr

    sanic_app.ctx.redicache = RedisCacheStoreStrategy()
    redis = Redis.from_url(profile.vector_store.redis_url)
    sanic_app.ctx.temp_repo = TemplateRepo(RedisTemplateProvider(redis))
    sanic_app.add_task(sql_emitter.aloop_drain(), name="sql_emitter_drain_loop")
    sanic_app.add_task(task_manager.schedule, name="task_scheduler_loop")


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
