"""
engine module
"""
import abc

from kbgpt.lib.templates.personality.models import PersonalityRepo
from kbgpt.lib.templates.rendering.models import TemplateRepo

# class Op(metaclass=abc.ABCMeta):
#     """
#     Operand
#     """

#     @abc.abstractmethod
#     def perform(self) -> 'Op':
#         """ perform the action undertaken """


# class OpPersonality(Op):

#     def perform(self):
#         pass


# class Operator(Op):
#     """
#     Operator
#     """

#     @property
#     @abc.abstractmethod
#     def operands(self) -> List[Op]:
#         """ list of child operations """


class Engine(metaclass=abc.ABCMeta):
    """ engine """

    @abc.abstractmethod
    async def agenerate(self) -> str:
        """ generate the template """


class CommentEngine(Engine):
    """ comment engine """

    def __init__(self):
        super().__init__()
        self.p_repo = PersonalityRepo.from_file("virtual_comment")
        self.temp = TemplateRepo().pick_one(name="comment")

    async def agenerate(self, *args, **kwargs) -> str:
        v_person = self.p_repo.pick_one()
        rendered = self.temp.render(*args, personality=v_person, **kwargs)
        return rendered


class SimpleEngine(Engine):
    """ clasify engine """

    def __init__(self, name:str) -> None:
        super().__init__()
        self.temp = TemplateRepo().pick_one(name=name)

    async def agenerate(self, *args, **kwargs) -> str:
        rendered = self.temp.render(*args, **kwargs)
        return rendered
