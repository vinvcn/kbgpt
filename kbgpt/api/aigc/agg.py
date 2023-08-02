import csv
from typing import Optional, Tuple

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel
from sanic import Blueprint, Request

from config import profile
from kbgpt.lib.llm.openai import Message, OpenAI

AGG = Blueprint("agg", url_prefix="agg")


class AGGRequest(BaseModel):
    history: Optional[Tuple[Message, ...]]
    question: str


async def gen_prompt(tname, data={}, inquiry=""):
    env = Environment(loader=FileSystemLoader(searchpath="./kbgpt/res"))
    prompt = env.get_template(tname).render(**{"products": data, "inquery": inquiry})
    openai = OpenAI()
    result = await openai.chat_completion(
        profile.generative_model, tuple([Message(role="system", content=prompt)])
    )
    return result


def make_json(csvFilePath):
    data = []

    # Open a csv reader called DictReader
    with open(csvFilePath, encoding="utf-8") as csvf:
        csvReader = csv.DictReader(csvf, delimiter="\t")

        # Convert each row into a dictionary
        # and add it to data
        for rows in csvReader:
            # Assuming a column named 'No' to
            # be the primary key
            data.append(rows)

    return data


async def score():
    inquiry = "Which Fund should I buy?"
    data = make_json("./kbgpt/res/productsintent.csv")
    result = await gen_prompt("step1.txt", data=data, inquiry=inquiry)
    print(result.content)


@AGG.route("/agg", methods=["GET"])
async def agg(request: Request, body: AGGRequest):
    jinja = Environment(loader=FileSystemLoader("./kbgpt/res/"))
    jinja.get_template("agg_step1.txt").render_async()
