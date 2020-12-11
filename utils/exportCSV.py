import csv, json, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from redisDB.redis_wrapper import RedisDB
# os.chdir(os.path.dirname(__file__))

CSV_RESULT_PATH = '../TEST_RESULT/result.csv'
LAUNCH_CONF_PATH = '../launch_conf.json'
REDIS_HASHNAME = 'ocr_result'

with open(LAUNCH_CONF_PATH) as f:
    launch_conf_dict = json.load(f)
    redis_config = launch_conf_dict["Redis_Config"]

redis_conn = RedisDB(config=redis_config)
result_dict = redis_conn.get_hash(REDIS_HASHNAME)

## create csv ##

headers = ['Image','GroundTruth','Prediction','MaxSimilar','TimeCost','AllResult','TaskDone']
rows_all = []
for key, val in result_dict.items():
    one_row = []
    one_row.append(key)
    one_row.extend(val.split('$'))
    rows_all.append(one_row)

if result_dict:
    # result sorted by time
    sorted_by_time = sorted(rows_all, key=lambda x:x[-1])
    with open(CSV_RESULT_PATH, 'w', encoding='utf-8') as f:
        f_csv = csv.writer(f)
        f_csv.writerow(headers)
        f_csv.writerows(sorted_by_time)
    print("Converted all result into csv file")

    ## delete all
    redis_conn.delete(REDIS_HASHNAME)
    print("Successfully deleted all result in redis")

else:
    print("No result found in redis")

