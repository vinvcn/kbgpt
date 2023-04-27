import asyncio

from config import profile
from kbgpt.lib.db.cache_store import RedisCacheStoreStrategy
from kbgpt.svc.qa_services import QAagent

cache = RedisCacheStoreStrategy.get_instance()
# agent = QAagent.get_instance()
# questions = ["what is SIP?", "What does SIP mean?" "What SIP is?"]
# asyncio.run(agent.answer_question_in_batch(questions, 2))

asyncio.run(cache.backup())
asyncio.run(cache.warmup())
