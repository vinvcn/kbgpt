"""
utility functions
"""
from functools import reduce
from typing import List
from langchain.callbacks.manager import OpenAICallbackHandler
import tiktoken

MODEL_COST_PER_1K_TOKENS = {
    "gpt-4": 0.03,
    "gpt-4-0314": 0.03,
    "gpt-4-completion": 0.06,
    "gpt-4-0314-completion": 0.06,
    "gpt-4-32k": 0.06,
    "gpt-4-32k-0314": 0.06,
    "gpt-4-32k-completion": 0.12,
    "gpt-4-32k-0314-completion": 0.12,
    "gpt-3.5-turbo": 0.002,
    "gpt-3.5-turbo-0301": 0.002,
    "text-ada-001": 0.0004,
    "ada": 0.0004,
    "text-babbage-001": 0.0005,
    "babbage": 0.0005,
    "text-curie-001": 0.002,
    "curie": 0.002,
    "text-davinci-003": 0.02,
    "text-davinci-002": 0.02,
    "code-davinci-002": 0.02,
}

MODEL_LIMIT_PER_MINUTE = {
    "gpt-3.5-turbo" : 90000 - 40000,
    "gpt-3.5-turbo-0301": 90000 - 40000
}


def tokenize(model_name: str, text: str) -> str:
    """ tokenize the given text """
    # create a GPT-3.5-Turbo encoder instance
    enc = tiktoken.encoding_for_model(model_name)
    # encode the text using the GPT-3.5-Turbo encoder
    tokenized_text = enc.encode(text)
    return tokenized_text


def token_counts(model_name:str, text: str) -> int:
    """ get the token counts """
    return len(tokenize(model_name, text))


def get_openai_token_cost_for_model(
    model_name: str, num_tokens: int, is_completion: bool = False
) -> float:
    """get the cost for given model and number of tokens"""
    suffix = "-completion" if is_completion and model_name.startswith("gpt-4") else ""
    model = model_name.lower() + suffix
    if model not in MODEL_COST_PER_1K_TOKENS:
        raise ValueError(
            f"Unknown model: {model_name}. Please provide a valid OpenAI model name."
            "Known models are: " + ", ".join(MODEL_COST_PER_1K_TOKENS.keys())
        )
    return MODEL_COST_PER_1K_TOKENS[model] * num_tokens / 1000


def get_total_cost(model_name: str, prompt_token: int, completion_token: int) -> float:
    """get the cost for given model and number of tokens"""
    return sum(
        (
            get_openai_token_cost_for_model(
                model_name, prompt_token, is_completion=False
            ),
            get_openai_token_cost_for_model(
                model_name, completion_token, is_completion=True
            ),
        )
    )


def get_total_cost_for_text(model_name: str, prompt: str, completion:str) -> float:
    """ get cost for text """
    prompt_counts = token_counts(model_name, prompt)
    completion_counts = token_counts(model_name, completion)
    return get_total_cost(model_name, prompt_counts, completion_counts)


def merge_stats(
    stats_a: OpenAICallbackHandler, stats_b: OpenAICallbackHandler
) -> OpenAICallbackHandler:
    """
    merge two stats
    """
    if not stats_a:
        return stats_b
    elif not stats_b:
        return stats_a
    else:
        stat = OpenAICallbackHandler()
        stat.total_tokens=stats_a.total_tokens + stats_b.total_tokens
        stat.prompt_tokens=stats_a.prompt_tokens + stats_b.prompt_tokens
        stat.completion_tokens=stats_a.completion_tokens + stats_b.completion_tokens
        stat.successful_requests=stats_a.successful_requests + stats_b.successful_requests
        stat.total_cost=stats_a.total_cost + stats_b.total_cost
        return stat


def merge_all_stats(stats_list:List[OpenAICallbackHandler]) -> OpenAICallbackHandler:
    """
    merge all stats
    """
    return reduce(merge_stats, stats_list)
