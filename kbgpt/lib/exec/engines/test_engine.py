import json
import logging
from typing import Any, Dict

from kbgpt.lib.exec.engines.configs.models import TestMod

from .engine import Engine


class TestEngine(Engine):
    def __init__(self, confg: TestMod) -> None:
        super().__init__(confg)

    async def agenerate(self, **kwargs) -> Dict[str, Any]:
        logging.info("params:\n%s", json.dumps(kwargs))
        for k in self.config.input_keys:
            assert k in kwargs, f"key '{k}' must be present in params"
            logging.info("reading input value: %s", kwargs[k])

        return self.config.output
