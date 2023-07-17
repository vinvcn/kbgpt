"""
base model module
"""

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """error response"""

    success: bool = Field(False)
    error: str = Field(None)

    def dict(self, *args, **kwargs):
        return super().dict(*args, exclude_none=True, **kwargs)

    def json(self, *args, **kwargs):
        return super().json(*args, exclude_none=True, indent=4, **kwargs)


class ResponseBase(BaseModel):
    """ response base """

    success: bool = Field(True)



class OpenAIResponseBase(ResponseBase):
    """base class of api response"""

    prompt_tokens: int = Field(0, exclude=True)
    comp_tokens: int = Field(0, exclude=True)
    total_tokens: int = Field(0, exclude=True)
    cost: float = Field(0.0, exclude=True)
