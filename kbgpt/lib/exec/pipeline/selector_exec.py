import logging
from collections import OrderedDict
from typing import Any, Dict

from kbgpt.lib.exec.pipeline.graph_models import ExecutionContext
from kbgpt.lib.exec.pipeline.selector_models import (
    MultiplexerType,
    Selector,
    SelectorMultiplexer,
)


class SelectorExec:
    multisel: SelectorMultiplexer

    def __init__(self, multisel: SelectorMultiplexer) -> None:
        self.multisel = multisel

    async def exec(self, ctx: ExecutionContext):
        hit_dict: Dict[str, Any] = OrderedDict()
        miss_dict: Dict[str, Selector] = OrderedDict()
        if not self.multisel:
            return hit_dict, miss_dict

        for selector in self.multisel.selectors:
            if (
                selector.node not in ctx.outputs
                or selector.key not in ctx.outputs[selector.node]
            ):
                logging.debug(
                    "node '%s', key '%s' missing", selector.node, selector.key
                )
                if selector.to_key:
                    miss_dict[selector.to_key] = selector
                else:
                    miss_dict[selector.key] = selector
            else:
                if selector.to_key:
                    assert (
                        selector.to_key not in hit_dict
                    ), f"output key '{selector.to_key}' conflict"
                    hit_dict[selector.to_key] = ctx.outputs[selector.node][selector.key]
                else:
                    assert (
                        selector.key not in hit_dict
                    ), f"default output key '{selector.key}' conflict"
                    hit_dict[selector.key] = ctx.outputs[selector.node][selector.key]

        assert len(hit_dict) > 0, "at least one value should present"

        if self.multisel.mode == MultiplexerType.FIRST:
            return dict((hit_dict.popitem(0),)), miss_dict
        elif self.multisel.mode == MultiplexerType.SOME:
            return dict(hit_dict), miss_dict
        else:
            assert not miss_dict, (
                f"multiplexer type is {self.multisel.mode},"
                + f" but {miss_dict} are missing"
            )
            return dict(hit_dict), miss_dict
