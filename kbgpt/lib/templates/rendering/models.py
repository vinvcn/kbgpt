"""
template rendering 
"""
import importlib
from typing import List

from pydantic import BaseModel

from kbgpt.lib.templates.constants import REPO_DIR


class Template(BaseModel):
    """ template model """

    template: str

    keywords: List[str]

    def render(self, *args, **kwargs) -> str:
        """ rendering the template """
        if len(args) + len(kwargs.keys()) > len(self.keywords):
            raise ValueError("Number of argument does not match")
        for k in kwargs:
            if k not in self.keywords:
                raise ValueError(f"key {k} is not expected. ")
        params = dict(zip(self.keywords[:len(args)], args))
        params.update(kwargs)
        return self.template.format(**params)


class TemplateRepo:
    """ template repository """

    def pick_one(self, name:str) -> Template:
        """ load from file """
        repo_mod_path = ".".join(self.__module__.split(".")[:-1] + [REPO_DIR, name])
        mod = importlib.import_module(repo_mod_path)
        return Template(template=mod.TEMPLATE, keywords=mod.KEYWORDS)
