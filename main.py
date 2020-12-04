import json, time
from worker import Worker

if __name__ == '__main__':
    ## TODO: dynamic add worker: add arg lauch_conf_path

    with open('launch_conf.json') as f:
        launch_conf_dict = json.load(f)
        worker_dict = launch_conf_dict["Worker_List"]
        mq_config = launch_conf_dict["MQ_Config"]
        redis_config = launch_conf_dict["Redis_Config"]

    process_list = []
    for gpu_idx, workers_info in worker_dict.items():
        for worker_id, switch in workers_info.items():
            p = Worker(mq_config, redis_config, gpu_idx, worker_id, switch)
            p.start()
            process_list.append(p)

    print('Workers is running ...')

    for p in process_list:
        p.join()

    print('Host process finished')