"""
web app
"""
from sanic import Sanic
from sanic.server.protocols.websocket_protocol import WebSocketProtocol

from config import profile
from kbgpt.api.libs.resources import ResourceMgr
from kbgpt.lib.db.cache_store import RedisCacheStoreStrategy
from kbgpt.lib.db.mysql import Crud
from kbgpt.lib.logging.mysql_emitter import MySqlEmitter

from .aigc import AIGC
from .legacy.apis import LEGACY

app = Sanic(profile.sanic.app_name)


app.blueprint(AIGC)
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

    await mgr.init_all()
    sanic_app.ctx.res = mgr

    sanic_app.ctx.redicache = RedisCacheStoreStrategy()
    sanic_app.add_task(sql_emitter.aloop_drain(), name="sql_emitter_drain_loop")


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
