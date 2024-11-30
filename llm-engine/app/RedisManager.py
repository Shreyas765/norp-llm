import redis


class RedisManager:
    def __init__(self, host="localhost"):
        """
        Initialize the Redis connection.

        Args:
            host (str): The host connection for redis.
        """
        redis_client = redis.Redis(
            host=host,
            port=6379,
            db=0,
            decode_responses=True
        )
        self.redis = redis_client
