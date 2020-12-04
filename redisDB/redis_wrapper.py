import redis
import logging
from retrying import retry

DEFAULT_REDIS_CONFIG = {
    'redis_host': '172.16.124.75',
    'redis_port': 6379,
    'db_index': 0,
    'retry_times': 3,
}

RETRY_TIMES = 3
RETRY_INTERVAL_SEC = 1

class RedisDB(object):

    TAG = "Redis"

    def __init__(self, config=None, tag=None):
        # log
        if tag is None:
            self.log = logging.getLogger(__name__)
        else:
            self.log = logging.getLogger("%s.%s" % (tag, RedisDB.TAG))

        self.host = config.get('redis_host')
        self.port = config.get('redis_port')
        self.db = config.get('db_index')
        self.retry_times = config.get('retry_times')

        global RETRY_TIMES
        RETRY_TIMES = self.retry_times

        try:
            self.r = redis.Redis(host=self.host, port=self.port, db=self.db, decode_responses=True, socket_connect_timeout=5)
            self.r.ping()
            print("Connection successful")
            self.log.info("Connection successful")
        except Exception as e:
            self.log.error("failed to init redisDB connection: ", exc_info=True)
            raise RuntimeError

    def __refresh_connect(self):
        try:
            self.r = redis.Redis(host=self.host, port=self.port, db=self.db, decode_responses=True, socket_connect_timeout=5)
            self.r.ping()
            print("Connection successful")
            self.log.info("Connection successful")
        except Exception as e:
            self.log.error("failed to init redisDB connection: ", exc_info=True)
            raise RuntimeError

#  = String OP =  #

    @retry(retry_on_result=lambda result: result is False,
           stop_max_attempt_number=RETRY_TIMES,
           wait_fixed=1000 * RETRY_INTERVAL_SEC)
    def insert(self, key, value):
        try:
            ret = self.r.set(key, value)
            return ret
        except Exception as e:
            self.__refresh_connect()
            self.log.error('failed to insert key <{}> and value <{}> error: <{}>'.format(key, value, e))
            return False

    @retry(retry_on_result=lambda result: result is None,
           stop_max_attempt_number=RETRY_TIMES,
           wait_fixed=1000 * RETRY_INTERVAL_SEC)
    def get(self, key):
        try:
            ret = self.r.get(key)
            return ret
        except Exception as e:
            self.__refresh_connect()
            self.log.error('failed to get key <{}> error: <{}>'.format(key, e))
            return None

    @retry(retry_on_result=lambda result: result is None,
           stop_max_attempt_number=RETRY_TIMES,
           wait_fixed=1000 * RETRY_INTERVAL_SEC)
    def delete(self, key):
        try:
            ret = self.r.delete(key)
            return ret
        except Exception as e:
            self.__refresh_connect()
            self.log.error('failed to delete key <{}> error: <{}>'.format(key, e))
            return None

# = hash OP = #

    @retry(retry_on_result=lambda result: result is False,
           stop_max_attempt_number=RETRY_TIMES,
           wait_fixed=1000 * RETRY_INTERVAL_SEC)
    def insert_hash(self, name, key, val):
        try:
            ret = self.r.hset(name, key, val)
            return ret
        except Exception as e:
            self.__refresh_connect()
            self.log.error('failed to insert name <{}> and hash <{},{}> error: <{}>'.format(name, key, val, e))
            return False

    @retry(retry_on_result=lambda result: result is None,
           stop_max_attempt_number=RETRY_TIMES,
           wait_fixed=1000 * RETRY_INTERVAL_SEC)
    def get_hash(self, name):
        try:
            ret = self.r.hgetall(name)
            return ret
        except Exception as e:
            self.__refresh_connect()
            self.log.error('failed to get name <{}> error: <{}>'.format(name, e))
            return None

    @retry(retry_on_result=lambda result: result is None,
           stop_max_attempt_number=RETRY_TIMES,
           wait_fixed=1000 * RETRY_INTERVAL_SEC)
    def del_hash(self, name, key):
        try:
            ret = self.r.hdel(name, key)
            return ret
        except Exception as e:
            self.__refresh_connect()
            self.log.error('failed to delete key <{}> from name <{}> error: <{}>'.format(key, name, e))
            return None


if __name__ == '__main__':
    redis_conn = RedisDB(config=DEFAULT_REDIS_CONFIG)
    # print(redis_conn.insert("0000.jpg", "abc bcd cde"))
    # print(redis_conn.get("0000.jpg"))
    # print(redis_conn.delete("0000.jpg"))
    name = "ocr_result"
    # key_1 = "0001.jpg"
    # val_1 = "asdbf/asdf/asdf/sdf/"
    #
    # key_2 = "0002.jpg"
    # val_2 = "nasdf/afdfe/ccvc/"
    # print(redis_conn.insert_hash(name, key_1, val_1))
    # print(redis_conn.insert_hash(name, key_2, val_2))
    # print(redis_conn.delete(name))
    dict_all = redis_conn.get_hash(name)
    print(dict_all)