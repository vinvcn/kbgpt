import openai
import pandas as pd
import asyncio
import re
import json
import random

from kbgpt.lib.templates.post_classification import CLASSFIER_TEMPLATE
from kbgpt.lib.templates.comments import TEMPLATE_ALL_WAYS, PERSONALITY, Personality

"""
As an arguer, you insist at questioning to make sense out of a topic. 
"""


async def classification(title, content):
    prompt = CLASSFIER_TEMPLATE.format(title=title, content=content)
    chat_completion = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}]
    )
    return chat_completion.choices[0].message['content']


async def submit_for_request(title, content):
    person = Personality.pick_one(PERSONALITY)
    print(person)
    prompt = TEMPLATE_ALL_WAYS.format(content=content, title=title, personality=person.expand())
    print(prompt)
    chat_completion = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}])
    ans_content = chat_completion.choices[0].message['content']
    print("---")
    print(ans_content)
    sub_ans = re.split('\r?\n', ans_content)
    sub_ans = [re.sub(r'^\d+\.\s+', "", ans) for ans in sub_ans if ans]
    return sub_ans[-1]


def title_n_content(fpath):
    df = pd.read_excel(fpath)
    for idx, row in df.iterrows():
        yield idx, row["Title"], row["Content"]

async def run_for_file():
    fpath = "/Users/admin/Projects/kbgpt/tools/Post.xlsx"
    opath = "/Users/admin/Projects/kbgpt/tools/Out.txt"
    cors = []
    for idx, title, content in title_n_content(fpath=fpath):
        if type(title) != str:
            title = ""
        cors.append(submit_for_request(title, content))
    
    gathered = await asyncio.gather(*cors)
    with open(opath, "w") as op:
        for l in gathered:
            op.write(f'{l}\n')
        
asyncio.run(run_for_file())


