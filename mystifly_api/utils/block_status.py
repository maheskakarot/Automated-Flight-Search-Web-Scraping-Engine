import redis

redis_host='10.10.0.4'
redis_port=6379

def redis_client():
    client = redis.StrictRedis(host=redis_host, port=redis_port)
    return client


def get_block_status():
    if redis_client().exists("wizzair_is_blocked"):
        return True
    else:
        return False
    
    
def set_block_status():

    if redis_client().exists("block_time"):
        pass
    else:
        redis_client().set('block_time',3600)

    block_time = redis_client().get('block_time')
    redis_client().set('wizzair_is_blocked', 'true', ex=int(block_time))
