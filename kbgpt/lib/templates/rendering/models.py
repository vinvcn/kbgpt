"""
template rendering 
"""
import importlib
from datetime import datetime
from typing import Any, Awaitable, Callable, List, Optional

from pydantic import BaseModel, Field

from kbgpt.lib.db.mysql import Crud
from kbgpt.lib.db.mysql.prompt_template import PromptTemplate
from kbgpt.lib.templates.constants import REPO_DIR


class Template(BaseModel):
    """template model"""

    template_id: str = Field("")
    body: str
    keywords: List[str]
    timestamp: Optional[datetime]

    @classmethod
    def from_orm(cls, orm: PromptTemplate) -> "Template":
        dictt = orm.__dict__.copy()
        dictt["keywords"] = [w.strip() for w in dictt["keywords"].split(",")]
        return Template(**dictt)

    def render(self, *args, **kwargs) -> str:
        """rendering the template"""
        if len(args) + len(kwargs.keys()) > len(self.keywords):
            raise ValueError("Number of argument does not match")
        for k in kwargs:
            if k not in self.keywords:
                raise ValueError(f"key {k} is not expected. ")
        params = dict(zip(self.keywords[: len(args)], args))
        params.update(kwargs)
        return self.body.format(**params)


class ModTemplateProvider:
    """module template provider"""

    async def __call__(self, *args: Any, template_id: str, **kwds: Any) -> Template:
        repo_mod_path = ".".join(
            self.__module__.split(".")[:-1] + [REPO_DIR, template_id]
        )
        mod = importlib.import_module(repo_mod_path)
        return Template(body=mod.TEMPLATE, keywords=mod.KEYWORDS)


class MySqlTemplateProvider:
    """template provider"""

    def __init__(self, crud: Crud):
        self.crud = crud

    async def __call__(self, *args: Any, template_id: str, **kwds: Any) -> Template:
        dct = {"template_id": template_id}
        return self.crud.get_first_by(
            cls=PromptTemplate,
            filter_params=dct,
            order_col="timestamp",
        )


class TemplateRepo:
    """template repository"""
    
    def __init__(self, provider: Callable[[str], Awaitable[Template]]):
        self.provider = provider

    async def pick_one(self, name: str) -> Template:
        return await self.provider(template_id=name)

    async def render(self, name: str, *args, **kwargs) -> str:
        temp_orm = await self.pick_one(name=name)
        if not temp_orm:
            raise ValueError(f"template name {name} not found")
        temp = Template.from_orm(temp_orm)
        return temp.render(*args, **kwargs)


MOD_TMP_REPO = TemplateRepo(ModTemplateProvider())
