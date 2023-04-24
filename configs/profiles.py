from pydantic import BaseModel, root_validator


class SuperConfig(BaseModel):
    @root_validator(pre=True)
    def check_and_convert_key_names(cls, values):
        """Convert all keys to lowercase"""
        print("validator called on value", values)
        return dict((k.lower(), v) for k, v in values.items())


class Sanic(SuperConfig):
    """Sanic configs"""

    port: int
    ip: str
    debug: bool
    workers: int


class QA(SuperConfig):
    """QA configs"""

    embeddings_model: str
    generative_model: str
    customer_service_temperature: float
    agent_cls: str


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
    redis_url: str
    pinecone_env: str
    chroma_persist_dir: str


class Cache(SuperConfig):
    """Cache configs"""

    use_redis_cache: bool
    redis_cache_similarity_threshold: float
    customer_service_cache_index: str


class Indexing(SuperConfig):
    """Indexing configs"""

    flush_before_write: bool
    customer_service_index: str


class Profile(SuperConfig):
    """Profile configs"""

    sanic: Sanic
    qa: QA
    embedding: Embedding
    vector_store: VectorStore
    cache: Cache
    indexing: Indexing
