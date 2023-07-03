"""
define the Sanic app
"""

from sanic import Blueprint

from kbgpt.api.aigc import comment, qa

LEGACY_QA = qa.QA.copy("legacy_qa", url_prefix="")
LEGACY_COMMENT = comment.COMMENT.copy("legacy_comment", url_prefix="")
LEGACY = Blueprint.group(LEGACY_QA, LEGACY_COMMENT)
