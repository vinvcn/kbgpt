import redis

from config import profile

# rds = redis.Redis.from_url(url=profile.report.redis_url,ssl=True)
rds = redis.StrictRedis(host="18.139.228.114", port="6380", db="0", ssl=True)
# "redis://:6380/0"

obj = rds.zrange(
    "kline:day:bfq:NSE-Nifty 50 Index",
    start=20230704000000,
    end=20230707000000,
    withscores=True,
    byscore=True
)

o_dic = {int(t[1]):t[0] for t in obj}

print(o_dic)
