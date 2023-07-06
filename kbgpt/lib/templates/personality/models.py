import abc
from enum import Enum
from functools import partial
from os.path import abspath, dirname, join
from random import choices, sample
from typing import List

from pydantic import BaseModel

from ..constants import REPO_DIR


class Indexer(BaseModel):
    """indexer"""

    index: int
    weight: float = 10.0


class RandomStrategy(Enum):
    """random strategy"""

    WEIGHT = 1
    RANDOM = 2


class Expandable(abc.ABC):
    """represents a class that can be expand to text"""

    @abc.abstractmethod
    def expand(self) -> str:
        """expand to text"""


class Emoji(BaseModel, Expandable):
    """emoji config"""

    weight: float = 10.0
    text: str = ""

    def expand(self) -> str:
        return self.text


class Tone(BaseModel, Expandable):
    """tone configuration"""

    weight: float = 10.0
    texts: List[str]

    def __add__(self, other):
        wt = min(self.weight, other.weight)
        tt = self.texts + other.texts
        return Tone(weight=wt, texts=tt)

    def expand(self) -> str:
        if not self.texts:
            return ""
        if len(self.texts) == 1:
            return self.texts[0]
        else:
            prefix = ", ".join(self.texts[:-1])
            return f"{prefix} and {self.texts[-1]}"


class Personality(BaseModel, Expandable):
    """personality"""

    name: str
    weight: float = 10.0
    personality: List[str]
    emoji: List[Emoji]
    tone_of_voice: List[Tone]

    def expand(self):
        """expand it to text"""
        per = sample(self.personality, 1)[0]
        if self.emoji:
            emo = choices(self.emoji, [e.weight for e in self.emoji])[0]
            emo = emo.expand()
        else:
            emo = ""
        if self.tone_of_voice:
            ton = choices(self.tone_of_voice, [t.weight for t in self.tone_of_voice])[0]
            ton = f"You are in a tone of {ton.expand()}."
        else:
            ton = ""
        return f"{per} {emo} {ton}"

    @staticmethod
    def pick_one(lst_of_persons):
        """randomly pick one from list"""
        lst: List[Personality] = lst_of_persons
        weights = [p.weight for p in lst]
        results = choices(lst, weights=weights)
        return results[0]


class PersonalityRepo(BaseModel):
    """personality repository"""

    p_list: List[Personality]

    strategy: RandomStrategy

    @staticmethod
    def from_file(name) -> 'PersonalityRepo':
        """ create repo from name """
        fname = f'{name}.json'
        cur_dir = dirname(abspath(__file__))
        fpath = join(cur_dir, REPO_DIR, fname)
        return PersonalityRepo.parse_file(fpath)

    def pick_one(self) -> Personality:
        """pick one"""
        choices_one = partial(choices, k=1)
        if self.strategy == RandomStrategy.RANDOM:
            return choices_one(self.p_list,k=1)[0]
        elif self.strategy == RandomStrategy.WEIGHT:
            weights = [p.weight for p in self.p_list]
            return choices_one(self.p_list, weights=weights, k=1)[0]
        else:
            raise ValueError(f"No such strategy {self.strategy}")
