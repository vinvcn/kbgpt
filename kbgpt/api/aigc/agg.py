import csv
import logging
from textwrap import indent
from typing import List, Optional, Tuple

from jinja2 import Environment, FileSystemLoader
from numpy import maximum
from pydantic import BaseModel, Field
from sanic import Blueprint, Request
from sanic_ext import openapi, validate

from config import profile
from kbgpt.api.constants import API_CONTENT_TYPE
from kbgpt.api.libs.base_model import ErrorResponse, ResponseBase
from kbgpt.api.libs.utils import jtext
from kbgpt.lib.llm.openai import Message, OpenAI
from kbgpt.svc.aigc.qa.qa_services import QAagent

AGG = Blueprint("agg", url_prefix="agg")

jinja = Environment(loader=FileSystemLoader("./kbgpt/res/"))


class AGGRequest(BaseModel):
    history: Optional[Tuple[Message, ...]]
    question: str
    threshold: int = Field(80)


class AGGResponse(ResponseBase):
    message: Optional[str]
    recommend: Optional[List[str]]
    product: Optional[str]


class Matching(BaseModel):
    name: str
    score: int = Field(..., le=100, ge=0)
    intent: str


class IntentResp(BaseModel):
    userInquiry: str
    userIntent: Optional[str]
    matching: Optional[List[Matching]]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.matching = sorted(self.matching, key=lambda item: item.score, reverse=True)


async def gen_prompt(tname, data={}, threshold=80, inquiry=""):
    prompt = jinja.get_template(tname).render(
        **{"products": data, "threshold": threshold, "inquery": inquiry}
    )
    print(prompt)
    openai = OpenAI()
    result = await openai.chat_completion(
        profile.generative_model, tuple([Message(role="system", content=prompt)])
    )
    print(result)
    return result


def make_json(csvFilePath):
    data = []

    # Open a csv reader called DictReader
    with open(csvFilePath, encoding="utf-8") as csvf:
        csvReader = csv.DictReader(
            csvf,
        )

        # Convert each row into a dictionary
        # and add it to data
        for rows in csvReader:
            # Assuming a column named 'No' to
            # be the primary key
            data.append(rows)

    return data


async def score(inquiry, threshold):
    data = make_json("./kbgpt/res/productsintent.csv")
    result = await gen_prompt(
        "agg_step1.txt", data=data, inquiry=inquiry, threshold=threshold
    )
    return IntentResp.parse_raw(result.content)


async def check_intent(inquery):
    result = await gen_prompt("agg_step0.txt", inquiry=inquery)
    return result.content.lower() == "yes"


async def get_product_by_intent(intent):
    data = make_json("./kbgpt/res/productsintent.csv")
    result = await gen_prompt("agg_step2.txt", data=data, inquiry=intent)
    return result.content


@AGG.route("/agg", methods=["POST"])
@openapi.description(
    "Get answer for the given question based on "
    + "similarity matching with the knowledge base"
)
@openapi.definition(body={API_CONTENT_TYPE: AGGRequest.schema()})
@openapi.response(
    200,
    {
        API_CONTENT_TYPE: AGGResponse.schema(),
    },
)
@openapi.response(500, {API_CONTENT_TYPE: ErrorResponse.schema()})
@validate(json=AGGRequest)
async def agg(request: Request, body: AGGRequest):
    try:
        if await check_intent(inquery=body.question):
            product = await get_product_by_intent(intent=body.question)
            return jtext(AGGResponse(product=product))
        else:
            intent = await score(inquiry=body.question, threshold=body.threshold)
            answer, _ = await QAagent.get_instance().answer_question(body.question)
            return jtext(
                AGGResponse(
                    message=answer,
                    recommend=[
                        itt.intent
                        for itt in intent.matching
                        if itt.score >= body.threshold
                    ],
                )
            )
    except Exception as e:
        logging.exception(e)
        return jtext(ErrorResponse(error=repr(e)))


if __name__ == "__main__":
    import asyncio

    # resp = asyncio.run(score("What are the classifications of funds?"))
    # print(resp.json(indent=4))
