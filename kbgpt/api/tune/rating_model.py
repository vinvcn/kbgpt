from typing import List, Optional

from pydantic import BaseModel, Field


class QuestionDto(BaseModel):
    id: int
    question: str
    rated: Optional[bool]


class ListQuestionDto(BaseModel):
    questions: List[QuestionDto]


class HumanRatingDto(BaseModel):
    id: Optional[int]
    question_id: int
    invoke_id: str
    node_id: str
    rater: str
    rating: str
    comment: Optional[str]


class RaterDto(BaseModel):
    id: Optional[int]
    name: str


class ForwardPrompt(BaseModel):
    prompt: str
    model: str
    temperature: float = Field(0.0)


class ListRaterDto(BaseModel):
    raters: List[RaterDto]
