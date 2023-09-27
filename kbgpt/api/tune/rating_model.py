from typing import List, Optional

from pydantic import BaseModel, Field, root_validator


class QuestionDto(BaseModel):
    id: int
    question: str
    rated: Optional[bool]


class ListQuestionDto(BaseModel):
    questions: List[QuestionDto]


class GetRaterPrompt(BaseModel):
    id: Optional[int]
    question_id: Optional[int]
    invoke_id: Optional[str]
    node_id: Optional[str]
    rater: Optional[str]
    debug_model: Optional[str]
    rater_prompt: Optional[str]
    rater_result: Optional[str]

    @root_validator(pre=True)
    def check_either_one_present(cls, values):
        """validator"""
        cond_fields = ["question_id", "invoke_id", "node_id", "rater"]
        id_present = "id" in values
        conditions_present = all([k in values for k in cond_fields])
        assert (
            id_present or conditions_present
        ), f" either 'id' or '{cond_fields}' should present"
        return values


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
