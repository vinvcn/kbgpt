from kbgpt.lib.exec.exec import *

json_config = """
{
    "nodes": [
        {
            "engine": {
                "type": "report_engine",
                "name": "report_daily",
                "render_config": {
                    "coverBreakSec": 1.7,
                    "pageBreakSec": 1,
                    "listingBreakSec": 1
                }
            },
            "pass_through": true,
            "in_keys": [
                "dt",
                "req",
                "name"
            ]
        },
        {
            "engine": {
                "type": "mapper_engine",
                "mapping": {
                    "content": "content"
                }
            },
            "pass_through": true,
            "in_keys": null
        },
        {
            "engine": {
                "type": "simple_engine",
                "name": "report.daily.adjust_space_and_breaks"
            },
            "pass_through": true,
            "in_keys": [
                "content"
            ]
        },
        {
            "engine": {
                "type": "mapper_engine",
                "mapping": {
                    "content": "content"
                }
            },
            "pass_through": true,
            "in_keys": null
        },
        {
            "engine": {
                "type": "simple_engine",
                "name": "report_polish"
            },
            "pass_through": true,
            "in_keys": [
                "content"
            ]
        },
        {
            "engine": {
                "type": "mapper_engine",
                "mapping": {
                    "content": "content"
                }
            },
            "pass_through": true,
            "in_keys": null
        }
    ]
}
"""

SerialPipe.parse_raw(json_config)
