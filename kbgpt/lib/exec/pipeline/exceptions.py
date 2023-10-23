import json
import logging
from os import environ

import aiohttp

from config import profile
from kbgpt.lib.exec.template_factory import JINJA_FS_ENV


class NodeExceptionHandler:
    async def handle(
        self, *, invoke_id=None, node=None, envs=None, exce=None, **kwargs
    ):
        pass


class DingtalkAlertHandler(NodeExceptionHandler):
    def render_temp(self, **kwargs):
        temp = JINJA_FS_ENV.get_template("dingtalk_alert_template.txt")
        return temp.render(**kwargs)

    async def handle(
        self, *, invoke_id=None, node=None, envs=None, exce=None, **kwargs
    ):
        if not profile.ops.alert.dingtalk_group:
            return

        msg = self.render_temp(
            env=environ["KBGPT_APP_ACTIVE_PROFILE"],
            invoke_id=invoke_id,
            node_id=repr(node.node),
            stacktrace=str(exce),
        )
        url = environ["DINGTALK_ALERT_WEBHOOK"]
        headers = {"Content-Type": "application/json"}
        data = {"msgtype": "markdown", "markdown": {"title": "券商AIGC报警", "text": msg}}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url, data=json.dumps(data)) as response:
                result_text = await response.text()
                logging.info(result_text)
