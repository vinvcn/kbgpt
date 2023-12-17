import abc
from typing import Any, Dict

import sqlalchemy
from sqlalchemy.orm import sessionmaker

from kbgpt.lib.db.mysql.mutual_funds import MFChatGPTReport
from kbgpt.lib.exec.engines.configs.models import FindRecentReportMod
from kbgpt.lib.exec.engines.engine import Engine


class FindRecentReport(Engine):
    """find recent report"""

    def __init__(self, mod: FindRecentReportMod) -> None:
        """init object"""
        super().__init__(mod)
        self.engine = sqlalchemy.create_engine(mod.connection_string, echo=False)

    @abc.abstractmethod
    async def agenerate(self, *, invoke_id=None, envs=None, **kwargs) -> Dict[str, Any]:
        """generate the template"""
        assert "mf_id" in kwargs, "mutual fund id must be present in kwargs"
        with sessionmaker(bind=self.engine)() as session:
            top_report = (
                session.query(MFChatGPTReport.content)
                .filter(MFChatGPTReport.mf_id == kwargs["mf_id"])
                .order_by(MFChatGPTReport.timestamp.desc())
                .first()
            )
            if top_report:
                return top_report
            else:
                return "N/A"
