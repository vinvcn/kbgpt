from sanic import Blueprint, Request, response
from sanic_jinja2 import SanicJinja2

FE = Blueprint("fe", url_prefix="fe")


@FE.get("/chat")
async def handler(request: Request):
    return await response.file("kbgpt/fe/dist/index.html")
    # jinja: SanicJinja2 = request.app.ctx.jinja
    # return await jinja.render_async(
    #     "public/index.html", request=request, **{"seq": ["one", "two"]}
    # )
