"""
global variables for the web modules
"""
__all__ = ["app"]

from sanic import Sanic

from config import profile

app = Sanic(profile.sanic.app_name)
