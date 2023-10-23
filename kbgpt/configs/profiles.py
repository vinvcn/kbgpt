from typing import List, Literal, Optional, Tuple

from pydantic import AnyUrl, BaseModel, Field, RedisDsn, root_validator


class SuperConfig(BaseModel):
    """Base class for all configs"""

    class Config:
        """Config for all configs"""

        allow_mutation = False
        validate_assignment = True

    @root_validator(pre=True)
    def check_and_convert_key_names(cls, values):
        """Convert all keys to lowercase"""
        return dict((k.lower(), v) for k, v in values.items())


class OpenAI(SuperConfig):
    """openai configuration"""

    proxied: bool = Field(False)
    proxy_url: Optional[AnyUrl]
    api_base_url: Optional[AnyUrl]
    unproxied_url: Optional[AnyUrl]


class AzureAI(SuperConfig):
    """azure configuration"""

    api_base: AnyUrl
    api_version: str
    env_key_name: Optional[str]
    deployments: List[str]


class Sanic(SuperConfig):
    """Sanic configs"""

    app_name: str
    port: int = Field(8081)
    ip: str = Field("0.0.0.0")
    debug: bool = Field(False)
    workers: int = Field(1)
    response_timeout: int = Field(300)


class Recomm(SuperConfig):
    gpt4_model: str
    gpt3_5_model: str


class QA(SuperConfig):
    """QA configs"""

    business_type: Literal["qa"] = Field("qa")
    embeddings_model: str
    generative_model: str
    recomm: Tuple[str, ...]
    customer_service_temperature: float
    request_timeout: int
    request_retry: int
    agent_cls: str
    words_limit: int = Field(..., gt=1, lt=1000)
    keep_msg_history: bool
    redis_index: str


class COMMENT(SuperConfig):
    """Comment Configs"""

    generative_model: str


class Embedding(SuperConfig):
    """Embedding Configs"""

    embedding_dimensions: int
    text_embedding_chunk_size: int
    text_embedding_chunk_overlap: int
    embeddings_function: str


class VectorStore(SuperConfig):
    """Vector Store configs"""

    vector_store_class: str
    vector_retrival_k: int
    redis_url: RedisDsn
    pinecone_env: str
    chroma_persist_dir: str


class Cache(SuperConfig):
    """Cache configs"""

    use_redis_cache: bool
    redis_cache_similarity_threshold: float
    customer_service_cache_index: str
    cool_down_seconds: int
    fresh_batch_size: int
    global_enabled: bool


class Sentiment(SuperConfig):
    """sentiment analysis"""

    analysis_model: str


class Report(SuperConfig):
    """market report"""

    backend_admin_url: AnyUrl
    trending_url: AnyUrl
    openai_model: str
    gpt_4_model: str


class ProductCatalog(SuperConfig):
    """product catalog configuration"""

    vector_store_class: str
    product_retrieval_k: int
    redis_index_name: str


class Alert(SuperConfig):
    """alert config"""

    dingtalk_group: bool


class OPS(SuperConfig):
    """operation config"""

    alert: Alert


class Profile(SuperConfig):
    """Profile configs"""

    sanic: Sanic
    comment: COMMENT
    sentiment: Sentiment
    report: Report
    qa: QA
    product_catalog: ProductCatalog
    amc_catalog: ProductCatalog
    embedding: Embedding
    vector_store: VectorStore
    cache: Cache
    db_url: AnyUrl
    generative_model: str
    openai: OpenAI
    azureai: List[AzureAI]
    baseurl: AnyUrl
    ops: OPS
    name: str = Field("DEFAULT")
