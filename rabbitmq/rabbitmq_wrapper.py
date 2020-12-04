# coding=utf-8

import pika
import requests, logging
from retrying import retry

DEFAULT_MQ_CONFIG = {
    'rmq_host': '172.16.124.75',
    'rmq_port': 5672,
    'vhost': '/',
    'username': 'guardstrike',
    'password': 'iiisct',
    'rest_port': 15672,
    'retry_times': 3,
}

RETRY_TIMES = 3
RETRY_INTERVAL_SEC = 1


class RabbitMQ(object):

    TAG = "RabbitMQ"

    def __init__(self, config=None, tag=None):

        # log
        if tag is None:
            self.log = logging.getLogger(__name__)
        else:
            self.log = logging.getLogger("%s.%s" % (tag, RabbitMQ.TAG))

        if config is None:
            config = DEFAULT_MQ_CONFIG

        self.host = config.get('rmq_host')
        self.port = config.get('rmq_port')
        self.vhost = config.get('vhost')
        self.username = config.get('username')
        self.password = config.get('password')
        self.rest_port = config.get('rest_port')
        self.retry_times = config.get('retry_times')

        global RETRY_TIMES
        RETRY_TIMES = self.retry_times

        self.connect = None
        self.channel = None

        try:
            conn_params = pika.ConnectionParameters(
                self.host,
                self.port,
                self.vhost,
                credentials=pika.credentials.PlainCredentials(self.username, self.password))

            self.connect = pika.BlockingConnection(conn_params)
            self.channel = self.connect.channel()
            self.log.info("Connection successful")

        except Exception as e:
            print('failed to init rabbitmq connection, error: <{}>'.format(e))
            self.log.error("failed to init rabbitmq connection: ", exc_info=True)
            raise RuntimeError

    def __refresh_connect(self):
        try:
            conn_params = pika.ConnectionParameters(
                self.host,
                self.port,
                self.vhost,
                credentials=pika.credentials.PlainCredentials(self.username, self.password))

            self.connect = pika.BlockingConnection(conn_params)
            self.channel = self.connect.channel()
        except Exception as e:
            print('failed to init rabbitmq connection, error: <{}>'.format(e))
            self.log.error("failed to init rabbitmq connection: ", exc_info=True)
            raise RuntimeError

    @retry(retry_on_result=lambda result: result is False,
           stop_max_attempt_number=RETRY_TIMES,
           wait_fixed=1000 * RETRY_INTERVAL_SEC)
    def fetch_a_msg_from_queue(self, queue_name, delete_msg=True):
        try:
            method, _, body = self.channel.basic_get(queue_name)
            if method:
                if delete_msg:
                    self.channel.basic_ack(method.delivery_tag)
                    return method, body
            return method, body

        except Exception as e:
            self.__refresh_connect()
            print('failed to fetch msg from queue <{}>, error: <{}>'.format(queue_name, e))
            self.log.error('failed to fetch msg from queue <{}>, error: <{}>'.format(queue_name, e))
            return False

    def ack_msg(self, method):
        self.channel.basic_ack(method.delivery_tag)

    def reject_msg(self, method):
        self.channel.basic_reject(method.delivery_tag)

    @retry(retry_on_result=lambda result: result is False,
           stop_max_attempt_number=RETRY_TIMES,
           wait_fixed=1000 * RETRY_INTERVAL_SEC)
    def send_a_msg_to_queue(self, queue_name, msg):
        try:
            self.channel.queue_declare(queue=queue_name,
                                       durable=True,
                                       exclusive=False,
                                       auto_delete=False)

            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=msg,
                properties=pika.BasicProperties(delivery_mode=2)
            )

            return True
        except Exception as e:
            self.__refresh_connect()
            print('failed to send msg <{}> to queue <{}>, error: <{}>'.format(queue_name, msg, e))
            self.log.error('failed to send msg <{}> to queue <{}>, error: <{}>'.format(queue_name, msg, e))

        return False

    @retry(retry_on_result=lambda result: result is None,
           stop_max_attempt_number=RETRY_TIMES,
           wait_fixed=1000 * RETRY_INTERVAL_SEC)
    def get_queue_msg_number(self, queue_name):
        try:
            queue = self.channel.queue_declare(
                queue=queue_name,
                durable=True,
                exclusive=False,
                auto_delete=False)

            return queue.method.message_count

        except Exception as e:
            self.__refresh_connect()
            print('failed to get queue <{}> msg number, error: <{}>'.format(queue_name, e))
            self.log.error('failed to get queue <{}> msg number, error: <{}>'.format(queue_name, e))

        return None

    @retry(retry_on_result=lambda result: result is None,
           stop_max_attempt_number=RETRY_TIMES,
           wait_fixed=1000 * RETRY_INTERVAL_SEC)
    def get_que_list(self, sort_by_msg_num=False):
        que_list = []
        url = 'http://%s:%s/api/queues/' % (self.host, self.rest_port)
        try:
            response = requests.get(url, auth=(self.username, self.password))
            que_list = [q for q in response.json()]
            if sort_by_msg_num:
                que_list.sort(key=lambda q: (q['messages']), reverse=True)

        except Exception as e:
            print('failed to get queue name list, error: <{}>'.format(e))
            self.log.error('failed to get queue name list, error: <{}>'.format(e))
            return None


        return que_list

    def release(self):
        if self.channel:
            self.channel.close()

        if self.connect:
            self.connect.close()

    def is_alive(self):
        try:
            conn_params = pika.ConnectionParameters(
                self.host,
                self.port,
                self.vhost,
                credentials=pika.credentials.PlainCredentials(self.username, self.password))

            connect = pika.BlockingConnection(conn_params)
            if connect.is_open:
                return True
        except:
            return False


if __name__ == '__main__':
    r = RabbitMQ()
    queue_name = 'OCR'
    import json
    msg = {'img_path':'/mnt/media/users/fangcheng/worker_inference/test_lsvt/gt_3333.jpg'}
    msg = json.dumps(msg)
    print(r.send_a_msg_to_queue(queue_name, msg))
    # print(r.get_queue_msg_number(queue_name))
    # print(r.fetch_a_msg_from_queue(queue_name))
    # print([q['name'] for q in r.get_que_list()])
    r.release()
    print(r.is_alive())
