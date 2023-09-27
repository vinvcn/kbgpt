import pytest

from kbgpt.lib.exec.pipeline.selector_exec import KeyExec


@pytest.mark.asyncio
async def test_key_exec1():
    result = KeyExec("b.b.e").exec({"a": [1, {"a": 1}], "b": {"b": {"c": 3, "e": 4}}})
    assert result == 4


@pytest.mark.asyncio
async def test_key_exec2():
    result = KeyExec("a[0]").exec({"a": [1, {"a": 1}], "b": {"b": {"c": 3, "e": 4}}})
    assert result == 1
