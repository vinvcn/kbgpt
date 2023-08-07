import aiohttp
import asyncio
from time import perf_counter

start_time = perf_counter()
url = f"http://0.0.0.0:8081/get_comments"
one_req = {
    "title": "",
    "content": "How do external factors, such as changes in government regulations or taxes, impact the behavior of firms and consumers in microeconomics? People socialize and influence each other and share their views. What consumers eats, wears and believes are all learned by influence through family, friends and social environment. All these external factors impact behavior of firms as well as consumers. Due to government's regulations business may become exposed to decline in their respective production patterns. As the government occasionally changes rules and regulations regarding businesses, businesses need to update their data frequently, so that company data are audited continuously, regulated, and updated. Otherwise, could expose your company to massive penalties. Companies must stay updated on regulations to avoid penalties stay within the legal framework. Overall, government regulations play a crucial role in shaping the business environment and promoting ethical and responsible practice. Lack of resources & Ongoing challenging are major challenges faced by businesses. Government policy can influence interest rates, a rise in which increases the borrowing cost. Higher rates will lead to decreased consumer spending, and lower interest rates attract investment as businesses increase production. If the government increases the tax on a goods the consumer price increases, and sellers' price decreases. Further Taxation reduces the purchasing power of the people and it reduces their consumption. The decline in consumption leads to decrease in effective demand for the goods and services, which in turn affects the production of these commodities. #microeconomics",
}


def gen_posts(total: int = 100, batch_size: int = 100):
    """generate batch of posts"""
    acc = 0
    posts = []
    for _ in range(total):
        acc += 1
        one_req["post_id"] = acc
        posts.append(dict.copy(one_req))
        if len(posts) >= batch_size:
            yield posts
            posts = []

    if posts:
        yield posts


async def submit(session: aiohttp.ClientSession, url, posts):
    start = perf_counter()
    async with session.post(url, json=posts) as resp:
        json_resp = await resp.json()
        print(f"batch size {len(posts)} time {perf_counter() - start}")
        # print(f"total tokens {sum([])} total cost {}")
        return json_resp


async def main():
    async with aiohttp.ClientSession() as session:
        for chunk in gen_posts(20, 20):
            await submit(session, url, chunk)


asyncio.run(main())
print("--- %s seconds ---" % (perf_counter() - start_time))
