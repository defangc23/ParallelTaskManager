from multiprocessing import Process
from rabbitmq.rabbitmq_wrapper import RabbitMQ
from redisDB.redis_wrapper import RedisDB
from utils import logger
import time, datetime, sys, os, json

from ocr import ocr_recognition
from strmatch.matchcn import matchcn

class Worker(Process):

    def __init__(self, mq_config, redis_config, gpu_idx, worker_id, switch):
        super().__init__()
        self.mq_config = mq_config
        self.redis_config = redis_config
        self.gpu_idx = gpu_idx
        self.worker_id = worker_id
        self.fail_retry = 3
        self.switch = switch
        self.queue_name = self.worker_id.split("_")[0]
        self.tag = str(gpu_idx)+'-'+str(worker_id)

        self.FLAG_msg = True
        self.FLAG_mtime = None
        self.FLAG_taskdone = 0

    def heartbeat(self):
        pass

    def task_process(self, msg, ocr_detection_model, ocr_recognition_modelA, ocr_recognition_modelB, ocr_label_dict):
        ret = 0
        try:
            # parse message
            msg_str = msg.decode().strip()
            msg_dict = json.loads(msg_str)
            img_path = msg_dict['img_path']
            gtTarget = msg_dict['ground_truth']
            demo_mode = msg_dict['demo_mode']

            assert os.path.exists(img_path) == True, "Image path {} is not exist".format(img_path)

            # worker inference
            timeCost_A, strAllResult_A = ocr_recognition.ocr_recognition(img_path,
                                                                     ocr_detection_model,
                                                                     ocr_recognition_modelA,
                                                                     ocr_label_dict, 299, tag=self.tag) # modelA 299

            preTarget_A, maxSimilar_A = matchcn(gtTarget, strAllResult_A)
            preTarget, maxSimilar, timeCost, strAllResult = preTarget_A, maxSimilar_A, timeCost_A, strAllResult_A

            if maxSimilar_A != -1 and maxSimilar_A < 50.0:
                timeCost_B, strAllResult_B = ocr_recognition.ocr_recognition(img_path,
                                                                         ocr_detection_model,
                                                                         ocr_recognition_modelB,
                                                                         ocr_label_dict, 256, tag=self.tag)

                preTarget_B, maxSimilar_B = matchcn(gtTarget, strAllResult_B)
                if maxSimilar_B > maxSimilar_A:
                    preTarget, maxSimilar, timeCost, strAllResult = preTarget_B, maxSimilar_B, timeCost_B, strAllResult_B


            time_done = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if not demo_mode:
                str_list = [str(gtTarget), str(preTarget), str(maxSimilar), str(round(timeCost,2)), str(strAllResult), time_done]
            else:
                str_list = [str(-1), str(-1), str(-1), str(round(timeCost, 2)), str(strAllResult), time_done]

            val_predict = "$".join(str_list).strip()
            key_imgpath = img_path.split('/')[-1]
            name = "ocr_result"
            insert_stat = self.db.insert_hash(name, key_imgpath, val_predict)
            self.log.info("DB insert: {}  Task Result: {} ".format(insert_stat, val_predict))
            ret = 1

        except Exception as e:
            self.log.error("Task Process Error: ", exc_info=True)

        return ret

    def checkswitch(self):
        lauch_conf_path = './launch_conf.json'
        file_mtime = os.stat(lauch_conf_path).st_mtime
        # update switch status
        if file_mtime != self.FLAG_mtime:
            with open(lauch_conf_path) as f:
                launch_conf_dict = json.load(f)
                self.switch = launch_conf_dict['Worker_List'][self.gpu_idx][self.worker_id]
            self.FLAG_mtime = file_mtime

    def run(self):
        self.log = logger.get_logger(self.tag, level='info')
        self.log.info('Worker {} started'.format(self.tag))

        healthy = True
        fail_counter = 0

        # dependencies initialize
        try:
            self.mq = RabbitMQ(self.mq_config, tag=self.tag)
            self.db = RedisDB(self.redis_config, tag=self.tag)

            # model initialize
            ocr_detection_model, ocr_recognition_modelA, ocr_recognition_modelB, ocr_label_dict = ocr_recognition.init_ocr_model(self.gpu_idx, tag=self.tag)

        except Exception as e:
            self.log.error("worker run initial fail !")
            self.log.error("Error info: ", exc_info=True)
            healthy = False

        while healthy:
            self.heartbeat()

            try:
                self.checkswitch()
                if self.switch == 0:
                    self.log.warning('Worker {} is deleted, shutting down'.format(self.tag))
                    sys.exit(0)

                method, msg = self.mq.fetch_a_msg_from_queue(queue_name=self.queue_name, delete_msg=False)
                if msg:
                    self.log.info('\n\n Task fetched: {}'.format(msg))
                    ret = self.task_process(msg,
                                            ocr_detection_model,
                                            ocr_recognition_modelA,
                                            ocr_recognition_modelB,
                                            ocr_label_dict)

                    if ret:
                        self.mq.ack_msg(method)
                        self.FLAG_taskdone += 1
                        self.log.info('[Done: {}] Task processed successfully ! \n\n'.format(self.FLAG_taskdone))
                        self.FLAG_msg = True
                    else:
                        # delete messgae
                        # self.log.error('Task processed failed ! \n\n')

                        ## requeue message
                        self.mq.reject_msg(method)
                        raise RuntimeError('Task processed failed !')


                else:
                    if self.FLAG_msg:
                        self.log.info('No task in the queue {} , Waiting...'.format(self.queue_name))
                        self.FLAG_msg = False
                    time.sleep(3)

            except Exception as e:
                fail_counter += 1
                if fail_counter > self.fail_retry:
                    healthy = False
                    continue
                self.log.error("Fail {} times.".format(fail_counter))



        self.log.error("Worker {} is unhealthy, shutting down".format(self.tag))
        sys.exit(0)
