"""
utility functions
"""

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
