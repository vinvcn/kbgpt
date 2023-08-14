import csv
import functools
import logging
from typing import List, Optional

from jinja2 import Environment, FileSystemLoader
from langchain.callbacks.manager import AsyncCallbackManagerForLLMRun
from pydantic import ValidationError
from sanic import Blueprint
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from config import profile
from kbgpt.api.aigc.agg_models import AGGRequest, AGGResponse, IntentResp, Matching
from kbgpt.api.aigc.qa_models import QAResponse
from kbgpt.api.constants import API_CONTENT_TYPE
from kbgpt.api.libs.base_model import ErrorResponse
from kbgpt.api.libs.utils import jtext
from kbgpt.lib.llm.openai import Message, OpenAI
from kbgpt.svc.aigc.qa.qa_services import QAagent

AGG = Blueprint("agg", url_prefix="agg")

jinja = Environment(loader=FileSystemLoader("./kbgpt/res/"))


async def gen_prompt(tname, data={}, choice="", threshold=80, inquiry="", stream=False):
    prompt = jinja.get_template(tname).render(
        **{
            "products": data,
            "threshold": threshold,
            "inquery": inquiry,
            "choice": choice,
        }
    )
    openai = OpenAI()
    result = await openai.chat_completion(
        profile.qa.generative_model,
        tuple([Message(role="system", content=prompt)]),
        stream=stream,
    )
    logging.debug(f"\n{prompt}")
    logging.debug(f"\n{result.content}")
    return result


@functools.lru_cache
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


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(0),
    retry=retry_if_exception_type(ValidationError),
    reraise=True,
)
async def score(inquiry, threshold):
    data = make_json("./kbgpt/res/productsintent.csv")
    result = await gen_prompt(
        "agg_step1.txt", data=data, inquiry=inquiry, threshold=threshold
    )
    if result.content == "N/A":
        return None
    lst = [l.split(",") for l in result.content.split("\n")]
    return IntentResp(matching=[Matching(id=p[0], score=p[1]) for p in lst])


async def get_recommendation(choice_id: int):
    data = make_json("./kbgpt/res/productsintent.csv")
    choice = [row for row in data if int(row["id"]) == choice_id]
    if not choice:
        raise ValueError(f"given id {choice_id} not exists")

    result = await gen_prompt(
        "recom_01.txt", data=data, choice=choice[0]["name"], threshold=80
    )
    name_to_rows = {row["name"]: row for row in data}
    lst = [l.strip() for l in result.content.split("\n")]
    result_ids = [name_to_rows[n]["id"] for n in lst]
    return IntentResp(matching=[Matching(id=rid, score=0) for rid in result_ids])


async def check_intent(inquery):
    result = await gen_prompt("agg_step0.txt", inquiry=inquery)
    return result.content.lower() == "yes"


async def get_product_by_ids(ids: List[Matching]):
    ids_to_match = [m.id for m in ids]
    matched = [
        r
        for r in make_json("./kbgpt/res/productsintent.csv")
        if int(r["id"]) in ids_to_match
    ]
    return matched


async def bouncing_ask(
    ids: List[Matching], question: str, handler: Optional[AsyncCallbackManagerForLLMRun]
):
    ids = ids[:4]
    product = await get_product_by_ids(ids)
    inner_completion = ""
    async for stream_resp in await gen_prompt(
        "agg_step3.txt", data=product, inquiry=question, stream=True
    ):
        # role = stream_resp["choices"][0]["delta"].get("role", role)
        token = stream_resp["choices"][0]["delta"].get("content", "")
        inner_completion += token
        await handler.on_llm_new_token(token)
    return QAResponse(answer=inner_completion)


async def get_product_by_intent(intent):
    data = make_json("./kbgpt/res/productsintent.csv")
    result = await gen_prompt("agg_step2.txt", data=data, inquiry=intent)
    return result.content


# @AGG.route("/agg", methods=["POST"])
# @openapi.description(
#     "Get answer for the given question based on "
#     + "similarity matching with the knowledge base"
# )
# @openapi.definition(body={API_CONTENT_TYPE: AGGRequest.schema()})
# @openapi.response(
#     200,
#     {
#         API_CONTENT_TYPE: AGGResponse.schema(),
#     },
# )
# @openapi.response(500, {API_CONTENT_TYPE: ErrorResponse.schema()})
# @validate(json=AGGRequest)
# async def agg(request: Request, body: AGGRequest):
#     try:
#         if await check_intent(inquery=body.question):
#             product = await get_product_by_intent(intent=body.question)
#             return jtext(AGGResponse(product=product))
#         else:
#             intent = await score(inquiry=body.question, threshold=body.threshold)
#             answer, _ = await QAagent.get_instance().answer_question(body.question)
#             return jtext(
#                 AGGResponse(
#                     message=answer,
#                     recommend=[
#                         itt.intent
#                         for itt in intent.matching
#                         if itt.score >= body.threshold
#                     ],
#                 )
#             )
#     except Exception as e:
#         logging.exception(e)
#         return jtext(ErrorResponse(error=repr(e)))


if __name__ == "__main__":
    import asyncio

    # resp = asyncio.run(score("What are the classifications of funds?"))
    # print(resp.json(indent=4))
