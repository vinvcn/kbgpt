import asyncio
import csv

from jinja2 import Environment, FileSystemLoader

from config import profile
from kbgpt.lib.llm.openai import Message, OpenAI


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


def write_json(data, csvFilePath):
    with open(csvFilePath, encoding="utf-8", mode="w") as csvf:
        writ = csv.DictWriter(csvf, fieldnames=list(data[0].keys()))
        writ.writeheader()
        writ.writerows(data)


async def gen_prompt(tname, data={}, inquiry=""):
    env = Environment(loader=FileSystemLoader(searchpath="./ai_aggs"))
    prompt = env.get_template(tname).render(**{"products": data, "inquery": inquiry})
    openai = OpenAI()
    result = await openai.chat_completion(
        profile.generative_model, tuple([Message(role="system", content=prompt)])
    )
    return result


async def gen_hook():
    data = make_json("./ai_aggs/products.csv")
    result = await gen_prompt("step0.txt", data=data)
    data_map = {d["name"].strip(): d for d in data}

    print(result.content)
    for l in result.content.split("\n"):
        if l:
            name, intent = l.split(":")
            data_map[name.strip()]["intent"] = intent.strip()

    print(data_map)
    write_json(list(data_map.values()), "./ai_aggs/productsintent.csv")


async def score():
    inquiry = "Which Fund should I buy?"
    data = make_json("./ai_aggs/productsintent.csv")
    result = await gen_prompt("step1.txt", data=data, inquiry=inquiry)
    print(result.content)


asyncio.run(gen_hook())
