import logging
import re
from collections import OrderedDict
from typing import Any, Dict, List

from config import profile
from kbgpt.lib.exec.pipeline.constants import K_PROFILE
from kbgpt.lib.exec.pipeline.graph_models import ExecutionContext
from kbgpt.lib.exec.pipeline.selector_models import (
    Key,
    Ky,
    MultiplexerType,
    Selector,
    SelectorMultiplexer,
    Sub,
)


class KeyExec:
    def __init__(self, expression: str) -> None:
        self.parsed_keys = self._parse_key(expression)

    def _parse_key(self, expression: str) -> List[Key]:
        keys = []
        # Split the expression by dots (.)
        dots = re.split(r"\.", expression)
        for key in dots:
            # Check if the key contains square brackets []
            if "[" in key:
                # Extract the name before the square brackets
                name = key[: key.index("[")]
                # Extract the index inside the square brackets
                index = int(re.search(r"\[(.*?)\]", key).group(1))
                # Create a Sub object with the extracted index
                sub_obj = Sub(index)
                # Create a Ky object with the extracted name and Sub object
                ky_obj = Ky(name, sub_obj)
                # Append the Ky object to the keys list
                keys.append(ky_obj)
            else:
                # If no square brackets are found, create a Ky object with the key as the name
                obj = Ky(key)
                keys.append(obj)
        return keys

    def exec(self, output: Any):
        sub_obj = output
        for k in self.parsed_keys:
            sub_obj = k.get_from(sub_obj)
        return sub_obj


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
            # if K_PROFILE == selector.node:
            #     d_prof = profile.dict()
            #     split_key = selector.key.split(".")
            #     try:
            #         for k in split_key:
            #             d_prof = d_prof[k]
            #     except KeyError:
            #         pass
            #     else:
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
                key_exec = KeyExec(selector.key)
                if selector.to_key:
                    assert (
                        selector.to_key not in hit_dict
                    ), f"output key '{selector.to_key}' conflict"

                    hit_dict[selector.to_key] = key_exec.exec(
                        ctx.outputs[selector.node]
                    )
                else:
                    assert (
                        selector.key not in hit_dict
                    ), f"default output key '{selector.key}' conflict"
                    hit_dict[selector.key] = key_exec.exec(ctx.outputs[selector.node])

        assert len(hit_dict) > 0, "at least one value should present"

        # if self.multisel.mode == MultiplexerType.FIRST:
        #     return dict((hit_dict.popitem(0),)), miss_dict
        if self.multisel.mode == MultiplexerType.ANY:
            assert len(hit_dict) > 0, (
                f"multiplexer type is {self.multisel.mode}"
                + " at least one hit should present"
            )
            return dict(hit_dict), miss_dict
        else:
            assert not miss_dict, (
                f"multiplexer type is {self.multisel.mode},"
                + f" but {miss_dict} are missing"
            )
            return dict(hit_dict), miss_dict
