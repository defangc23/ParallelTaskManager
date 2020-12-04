import json
from collections import OrderedDict
import os, sys

d = OrderedDict()

d['Worker_List'] = {
    '0': {'OCR_0': 1},
    '1': {'OCR_1': 1},
    '2': {'OCR_2': 1},
    '3': {'OCR_3': 1},
}

d['MQ_Config'] = {
    'rmq_host': '172.16.124.75',
    'rmq_port': 5672,
    'vhost': '/',
    'username': 'guardstrike',
    'password': 'iiisct',
    'rest_port': 15672,
    'retry_times': 3,
}

dumped = json.dumps(d,indent=4)
with open('../launch_conf.json', 'w') as c:
    c.write(dumped)
