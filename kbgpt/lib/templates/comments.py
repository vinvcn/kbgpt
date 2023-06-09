from typing import List
from pydantic import BaseModel
from random import sample, choices
import abc
from functools import partial


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


class Indexer(BaseModel):
    """indexer"""

    index: int
    weight: float = 10.0


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


def index_and_update(tones: List[Tone], idx: Indexer) -> Tone:
    """select element from list and return"""
    return tones[idx.index].copy(update={"weight": idx.weight})


def select_and_merge(tones: List[Tone], ls_idx: List[Indexer]) -> Tone:
    """select all indexes and sum up"""
    if isinstance(ls_idx, Indexer):
        return index_and_update(tones, ls_idx)
    selected = [index_and_update(tones, idx) for idx in ls_idx]
    if selected:
        return sum(selected[:-1], selected[-1])
    else:
        return None


def select_indexes(tones: List[Tone], selectors: List[List[Indexer]]) -> List[Tone]:
    """select all indexes"""
    selected = [select_and_merge(tones, ls_idx) for ls_idx in selectors]
    return [sel for sel in selected if sel]




class Personality(BaseModel):
    """personality"""

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


EMO_NO = Emoji(text="", weight=5.0)
EMO_SOME = Emoji(text="You love to use emojis alot.", weight=20.0)
EMO_ALL = Emoji(text="You only use emojis in your reply.", weight=10.0)

EMOJI_LIST = [EMO_NO, EMO_SOME, EMO_ALL]

TONE_FRIENDLY = Tone(texts=["friendly"])
TONE_EXCITED = Tone(texts=["excited"])
TONE_ENCOURAGING = Tone(texts=["encouraging"])
TONE_PLAYFUL = Tone(texts=["playful"])
TONE_HUMOROUS = Tone(texts=["humorous"])
TONE_CONFIDENT = Tone(texts=["confident"])
TONE_PERSUASIVE = Tone(texts=["persuasive"])
TONE_PROFESSIONAL = Tone(texts=["professional"])
TONE_AUTHORITATIVE = Tone(texts=["authoritative"])
TONE_INFORMATIVE = Tone(texts=["informative"])
TONE_JOYFUL = Tone(texts=["joyful"])
TONE_INQUISITIVE = Tone(texts=["inquisitive"])
TONE_ANALYTICAL = Tone(texts=["analytical"])
TONE_SERIOUS = Tone(texts=["serious"])

TONE_LIST = [
    TONE_FRIENDLY,  # 0
    TONE_EXCITED,  # 1
    TONE_ENCOURAGING,  # 2
    TONE_PLAYFUL,  # 3
    TONE_HUMOROUS,  # 4
    TONE_CONFIDENT,  # 5
    TONE_PERSUASIVE,  # 6
    TONE_PROFESSIONAL,  # 7
    TONE_AUTHORITATIVE,  # 8
    TONE_INFORMATIVE,  # 9
    TONE_JOYFUL,  # 10
    TONE_INQUISITIVE,  # 11
    TONE_ANALYTICAL,  # 12
    TONE_SERIOUS,  # 13
]

select_and_sum = partial(select_indexes, TONE_LIST)

"""
friendly", "excited", "encouraging", "playful", "humorous"
"""
PER_CALL_ATT = Personality(
    personality=[
        "You don't know much about the topic, but you just want to call the attention of the audience."
    ],
    emoji=EMOJI_LIST,
    tone_of_voice=select_and_sum(
        [
            Indexer(index=0),
            Indexer(index=1),
            Indexer(index=2),
            Indexer(index=3),
            Indexer(index=4),
        ]
    ),
)


"""
confident", "persuasive", "professional", "authoritative", "informative",
"""
PER_INSIDER = Personality(
    personality=["You know something inside about it and you want to share it."],
    emoji=EMOJI_LIST,
    tone_of_voice=select_and_sum(
        [
            Indexer(index=5),
            Indexer(index=6),
            Indexer(index=7),
            Indexer(index=8),
            Indexer(index=9),
        ]
    ),
)

"""
playful", "joyful", "friendly", "excited"
"""
PER_SHARING = Personality(
    personality=["Generate some knowledge about the topic and share it."],
    emoji=EMOJI_LIST,
    tone_of_voice=select_and_sum(
        [
            Indexer(index=5),
            Indexer(index=6),
            Indexer(index=7),
            Indexer(index=8),
            Indexer(index=9),
        ]
    ),
)

"""
"playful", "joyful", "friendly", "excited"
"""
PER_DEMANDER = Personality(
    personality=["Appreciate it, and ask for more. "],
    emoji=EMOJI_LIST,
    tone_of_voice=select_and_sum(
        [Indexer(index=3), Indexer(index=10), Indexer(index=0), Indexer(index=1)]
    ),
)

"""
"joyful", "friendly", "excited"
"""
PER_PRAISER = Personality(
    personality=["Use less than 5 words to say thanks."],
    emoji=EMOJI_LIST,
    tone_of_voice=select_and_sum(
        [Indexer(index=10), Indexer(index=0), Indexer(index=1)]
    ),
)

"""
"friendly", "inquisitive", "joyful"
"""
PER_PICKER = Personality(
    personality=[
        "Find out something important that's missing and ask for it, using emoji. "
    ],
    emoji=EMOJI_LIST,
    tone_of_voice=select_and_sum(
        [Indexer(index=0), Indexer(index=11), Indexer(index=10)]
    ),
)

"""
"friendly", "inquisitive", "humorous"
"""
PER_LOCATE = Personality(
    personality=[
        "Pick a random state in india, tell that you are from there, and praise the post."
    ],
    emoji=EMOJI_LIST,
    tone_of_voice=select_and_sum(
        [Indexer(index=0), Indexer(index=11), Indexer(index=4)]
    ),
    weight=1.0,
)

"""
"analytical", "serious", "confident"
"""
TEMP_COT = """
You do it step by step:
1. Summarize the main topic of the content.
2. Extract the opinion and attitude on the topic. 
3. Extract the facts that's supporting the arguments.
4. Find out why and how the topic and the writting will be beneficial and helpful to readers.
5. Write a reply. The reply should include an ackownledgement to content creator and encourage the user to create more content.
"""
PER_ANALYTICAL = Personality(
    personality=[TEMP_COT],
    emoji=EMOJI_LIST,
    tone_of_voice=select_and_sum(
        [Indexer(index=12), Indexer(index=13), Indexer(index=5)]
    ),
)

PERSONALITY = [
    PER_CALL_ATT,
    PER_INSIDER,
    PER_SHARING,
    PER_DEMANDER,
    PER_PRAISER,
    PER_PICKER,
    PER_LOCATE,
    PER_ANALYTICAL,
]

TEMPLATE_ALL_WAYS = """
Now forget who you are. Your new role is human reading a post from a web forum, your job is to write a sentence for the post. 
{personality}


Post Content:
---

{title}

{content}

---

Your reply:
"""


def get_prompt_with_personality(title: str, content: str) -> str:
    """get prompt with personality"""
    person = Personality.pick_one(PERSONALITY)
    return TEMPLATE_ALL_WAYS.format(
        content=content, title=title, personality=person.expand()
    )
