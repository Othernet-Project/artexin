# -*- coding: utf-8 -*-
from hotqueue import HotQueue


class RedisQueueWrapper(object):
    """Wrapper class used to allow deferred initialization of a `HotQueue`
    instance."""
    _redis_queue = None

    def __call__(self):
        return self._redis_queue

    def setup(self, config):
        if self._redis_queue:
            return

        self._redis_queue = HotQueue("job_queue",
                                     host=config['redis.host'],
                                     port=config['redis.port'],
                                     password=config['redis.password'])


RedisQueue = RedisQueueWrapper()
