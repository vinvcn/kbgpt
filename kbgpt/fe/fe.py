from sanic import Blueprint, Request
from sanic_jinja2 import SanicJinja2

FE = Blueprint("fe", url_prefix="fe")


@FE.get("/chat")
async def handler(request: Request):
    jinja: SanicJinja2 = request.app.ctx.jinja
    return await jinja.render_async(
        "index.html", request=request, **{"seq": ["one", "two"]}
    )
