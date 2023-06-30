import functools
import inspect
import time
from typing import Callable, Type

from kbgpt.lib.db.mysql.base import OBase
from kbgpt.lib.logging.mysql_emitter import MySqlEmitter
from kbgpt.web.globals import app
from kbgpt.web.resources import ResourceMgr


def alog(record_type: Type[OBase]):
    """decorator to log function call using MySQLEmitter"""

    def wrapper(func: Callable):
        """wrapper"""
        sig = inspect.signature(func)
        defaults = {
            k: v.default if v.default is not inspect.Parameter.empty else None
            for k, v in sig.parameters.items()
        }
        argnames = list(func.__code__.co_varnames[: func.__code__.co_argcount])

        @functools.wraps(func)
        async def inner_wrapper(*args, **kwargs):
            """inner wrapper"""
            start_time = time.perf_counter()
            result = await func(*args, **kwargs)
            seconds_spent = time.perf_counter() - start_time
            args_dict = defaults.copy()
            args_dict.update(dict(zip(argnames[:len(args)], args)))
            args_dict.update(kwargs)
            obj = record_type.create(
                kwargs=args_dict, result=result, seconds_spent=seconds_spent
            )
            res: ResourceMgr = app.ctx.res
            emiter: MySqlEmitter = res.get(MySqlEmitter.__name__)
            await emiter.aemit(obj)
            return result

        return inner_wrapper

    return wrapper
