"""
tune api
"""
import csv
import functools
import logging
import time
from ast import match_case
from functools import partial
from json import dumps
from math import ceil
from multiprocessing.spawn import prepare
from os.path import join
from typing import List, Optional
from urllib.parse import unquote
from uuid import uuid4

from pydantic import BaseModel
from sanic import Blueprint, Request, json, text
from sanic_ext import openapi, validate
from sqlalchemy import and_
from sqlalchemy import text as stext
from sqlalchemy.orm import sessionmaker

from config import profile
from kbgpt.api.aigc.agg import (
    bouncing_ask,
    get_recommendation,
    get_recommendation_by_conversation,
    get_recommendation_by_name,
)
from kbgpt.api.aigc.agg_models import IntentResp, Matching
from kbgpt.api.aigc.qa_models import (
    DocInfo,
    GetRecomm,
    QAResponse,
    Question,
    RecommType,
)
from kbgpt.api.constants import API_CONTENT_TYPE
from kbgpt.api.libs.resources import ResourceMgr
from kbgpt.api.tune.rating_model import (
    ForwardPrompt,
    HumanRatingDto,
    ListQuestionDto,
    ListRaterDto,
    QuestionDto,
    RaterDto,
)
from kbgpt.lib.db.mysql import Crud
from kbgpt.lib.db.mysql.human_rating import HumanRating, Rater
from kbgpt.lib.db.mysql.jinja_engine_record import JinjaTemplateRecord
from kbgpt.lib.db.mysql.qa_record import QARecord
from kbgpt.lib.db.vector_store import BusinessType, create_vector_store_strategy
from kbgpt.lib.exec.pipeline.graph_exec import GraphExecutor
from kbgpt.lib.llm.openai import Message, client
from kbgpt.lib.logging.mysql_emitter import MySqlEmitter
from kbgpt.svc.aigc.qa.cache_qa_services import ProxiedQAAgent
from kbgpt.svc.aigc.qa.file_services import ProxiedDocAgent
from kbgpt.svc.aigc.qa.qa_graph import QA_GRAPH
from kbgpt.svc.aigc.qa.qa_services import QAagent
from kbgpt.svc.aigc.unified import AIGCAgent

RATE = Blueprint("rate", url_prefix="rate")


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


def tranform_recommend_products(content):
    if content.lower() == "n/a":
        return content
    fn = "./kbgpt/res/productsintent.csv"
    rows = make_json(fn)

    mapping = {r["id"]: r for r in rows}

    pid_lst = [s.strip() for s in content.split(",")]

    results = []
    for pid in pid_lst:
        row = mapping[pid]
        prepre = f"Product Name: {row['name']}"
        results.append(prepre)

    return "\n".join(results)


RST_MAPPER = {"qa.recommend_products": tranform_recommend_products}


class ListRating(BaseModel, orm_mode=True):
    rater: Optional[str]
    page: Optional[int]
    rating: Optional[int]


PER_PAGE = 10


def match_file_name(rating: str):
    fn = ""
    match rating:
        case "all" | None:
            fn = "find_all_questions.sql"
        case "rated":
            fn = "find_rated_questions.sql"
        case "unrated":
            fn = "find_not_rated_or_partially_rated_questions.sql"
        case _:
            raise ValueError(f"Invalid rating filter value {rating}")
    return fn


def match_file_name_turn_question(rating: str):
    fn = ""
    match rating:
        case "all" | None:
            fn = "next_question_all.sql"
        case "rated":
            fn = "next_question_rated.sql"
        case "unrated":
            fn = "next_question_unrated.sql"
        case _:
            raise ValueError(f"Invalid rating filter value {rating}")
    return fn


@RATE.route("/max_page", methods=["GET"])
async def max_page(request: Request):
    params = {k: v for k, v in request.get_query_args()}
    rater = params.get("rater", None)
    if rater:
        rater = unquote(rater)
    rating = params.get("rating", None)
    fn = match_file_name(rating)

    sql_text = read_sql(fn)
    sql_text = sql_text.format(rater=rater, columns="count(0)")
    res: ResourceMgr = request.app.ctx.res
    crud: Crud = res.get(Crud.__name__)
    with sessionmaker(bind=crud.engine)() as session:
        result = session.execute(stext(sql_text))
        count = result.scalar_one_or_none()
        max_page_no = ceil(count / PER_PAGE)
        return json({"max_page": max_page_no})


@functools.lru_cache
def read_sql(filename):
    dir_path = "./kbgpt/res/sql"
    full_path = join(dir_path, filename)
    with open(full_path, "r", encoding="utf-8") as fp:
        sql_text = fp.read()
        return sql_text


@RATE.route("/list_rating", methods=["GET"])
async def list_rating(request: Request):
    params = {k: v for k, v in request.get_query_args()}
    rater = params.get("rater", None)
    if rater:
        rater = unquote(rater)
    page = params.get("page", 1)
    if page:
        page = int(page)
    rating = params.get("rating", None)

    fn = match_file_name(rating)

    sql_text = read_sql(fn)
    sql_text = sql_text.format(rater=rater, columns="*")
    sql_text = sql_text + f" LIMIT {PER_PAGE} " + f" OFFSET {(page - 1) * PER_PAGE}"
    res: ResourceMgr = request.app.ctx.res
    crud: Crud = res.get(Crud.__name__)
    with sessionmaker(bind=crud.engine)() as session:
        results = session.query(QARecord).from_statement(stext(sql_text)).all()
        if results:
            qarecords = results
            dtos = ListQuestionDto(
                questions=[QuestionDto(**q.as_dict()) for q in qarecords]
            )
            return text(dtos.json(indent=4), content_type=API_CONTENT_TYPE)
        else:
            return text("{}")


@RATE.route("/next_rating", methods=["GET"])
async def get_next_question(request: Request):
    params = {k: v for k, v in request.get_query_args()}
    rater = params.get("rater", None)
    if rater:
        rater = unquote(rater)
    question_id = params.get("id")
    rating = params.get("rating", None)
    fn = match_file_name_turn_question(rating)

    sql_text = read_sql(fn)
    sql_text = sql_text.format(
        rater=rater, where_clause=f"id > {question_id}", order_by="id asc"
    )

    res: ResourceMgr = request.app.ctx.res
    crud: Crud = res.get(Crud.__name__)
    with sessionmaker(bind=crud.engine)() as session:
        record = session.query(QARecord).from_statement(stext(sql_text)).one_or_none()
        if not record:
            return json({})
        else:
            return json({"question_id": record.id})


@RATE.route("/prev_rating", methods=["GET"])
async def get_prev_question(request: Request):
    params = {k: v for k, v in request.get_query_args()}
    rater = params.get("rater", None)
    if rater:
        rater = unquote(rater)
    question_id = params.get("id")
    rating = params.get("rating", None)
    fn = match_file_name_turn_question(rating)
    sql_text = read_sql(fn)
    sql_text = sql_text.format(
        rater=rater, where_clause=f"id < {question_id}", order_by="id desc"
    )

    res: ResourceMgr = request.app.ctx.res
    crud: Crud = res.get(Crud.__name__)
    with sessionmaker(bind=crud.engine)() as session:
        record = session.query(QARecord).from_statement(stext(sql_text)).one_or_none()
        if not record:
            return json({})
        else:
            return json({"question_id": record.id})


@RATE.route("/rating/<qid:int>/<rater:str>", methods=["GET"])
async def get_question(request: Request, qid: int, rater: str):
    rater = unquote(rater)
    res: ResourceMgr = request.app.ctx.res
    crud: Crud = res.get(Crud.__name__)

    with sessionmaker(bind=crud.engine)() as session:
        results = (
            session.query(QARecord, JinjaTemplateRecord)
            .join(
                JinjaTemplateRecord, QARecord.invoke_id == JinjaTemplateRecord.invoke_id
            )
            .filter(QARecord.id == qid)
            .order_by(JinjaTemplateRecord.timestamp.asc())
            .all()
        )
        if results:
            result_dict = results[0][0].as_dict()
            steps_dict = []
            for q, j in results:
                rating = (
                    session.query(HumanRating)
                    .filter(
                        and_(
                            HumanRating.question_id == q.id,
                            HumanRating.node_id == j.node_id,
                            HumanRating.rater == rater,
                        )
                    )
                    .order_by(HumanRating.timestamp.desc())
                    .limit(1)
                    .one_or_none()
                )
                step_dict = j.as_dict()
                if rating:
                    step_dict.update(rating.as_dict())
                trans = RST_MAPPER.get(j.node_id, None)
                if trans:
                    step_dict["result"] = trans(step_dict["result"])
                steps_dict.append(step_dict)

            result_dict["steps"] = steps_dict
            return text(dumps(result_dict, default=str), content_type=API_CONTENT_TYPE)

    return text("{}")


@RATE.route("/rating", methods=["PUT"])
@openapi.description(
    "In streaming, get answer for the given question based on "
    + "similarity matching with the knowledge base"
)
@openapi.definition(body={API_CONTENT_TYPE: HumanRatingDto.schema()})
@validate(json=HumanRatingDto)
async def rate_it(request: Request, body: HumanRatingDto):
    res: ResourceMgr = request.app.ctx.res
    crud: Crud = res.get(Crud.__name__)
    row = HumanRating(**body.dict())
    if row.id:
        crud.update_rows(HumanRating, [row])
    else:
        crud.add(row)
    return json({"success": True})


@RATE.route("/rater", methods=["PUT"])
@openapi.description(
    "In streaming, get answer for the given question based on "
    + "similarity matching with the knowledge base"
)
@openapi.definition(body={API_CONTENT_TYPE: RaterDto.schema()})
@validate(json=RaterDto)
async def add_rater(request: Request, body: RaterDto):
    res: ResourceMgr = request.app.ctx.res
    crud: Crud = res.get(Crud.__name__)
    rater = Rater(**body.dict())
    if rater.id:
        crud.update_rows(Rater, [rater])
    else:
        crud.add(rater)
    return json({"success": True})


@RATE.route("/list_rater", methods=["GET"])
async def list_rater(request: Request):
    res: ResourceMgr = request.app.ctx.res
    crud: Crud = res.get(Crud.__name__)
    raters = crud.get_all(Rater)
    results = ListRaterDto(raters=[RaterDto(**r.as_dict()) for r in raters])
    return text(results.json(indent=4), content_type=API_CONTENT_TYPE)


@RATE.route("/forward_prompt", methods=["POST"])
@openapi.definition(body={API_CONTENT_TYPE: ForwardPrompt.schema()})
@validate(json=ForwardPrompt)
async def foward(request: Request, body: ForwardPrompt):
    # model: Union[str, Tuple[str, ...]],
    # messages: Tuple[Message, ...],
    completion = await client.chat_completion(
        model=body.model,
        messages=tuple([Message(role="system", content=body.prompt)]),
        temperature=body.temperature,
    )
    return json(
        {
            "success": True,
            "result": completion.content,
            "usage": completion.usage.dict(),
        }
    )
