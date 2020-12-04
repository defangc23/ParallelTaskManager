import json, glob, csv, os
from rabbitmq.rabbitmq_wrapper import RabbitMQ

class MQ_Sender(object):

    def __init__(self, mq_config):
        self.mq = RabbitMQ(mq_config)

    def send(self, queue_name, msg_dict):
        msg = json.dumps(msg_dict)
        stat = self.mq.send_a_msg_to_queue(queue_name, msg)
        print('msgStat:{}  msg:{}'.format(stat, msg))
        return stat

    def release(self):
        self.mq.release()

if __name__ == '__main__':

    LAUNCH_CONF_PATH = './launch_conf.json'
    QUEUE_NAME = 'OCR'

    FOLDER_LIST = ['0102','0103','0204','0205','0206','0307','0308','0309','0410','0411','0510','0513','0514','0615','0616','0617','0718','0719','0720','0721','0722','0723','0724']
    # FOLDER_LIST = ['0718']
    for n in FOLDER_LIST:
        TASK_FOLDER = '/mnt/media/users/fangcheng/test_img/OCR-POC/OCR/{}'.format(n)
        TASK_LABEL_CSV = '/mnt/media/users/fangcheng/test_img/OCR-POC/csv/{}.csv'.format(n)

        ## init rabbitmq
        with open(LAUNCH_CONF_PATH) as f:
            launch_conf_dict = json.load(f)
            mq_config = launch_conf_dict["MQ_Config"]
        sender = MQ_Sender(mq_config)

        ## send task
        sent_counter = 0
        with open(TASK_LABEL_CSV, encoding='utf-8') as f:
            reader = csv.reader(f)
            # header = next(reader)
            # print(header)
            for row in reader:
                complete_path_list = glob.glob(os.path.join(TASK_FOLDER, row[0])+'.*')
                if complete_path_list:
                    complete_path = complete_path_list[0]
                    send_stat = sender.send(QUEUE_NAME, {"img_path": complete_path, "ground_truth": row[1]})
                    if send_stat:
                        sent_counter += 1

        sender.release()
        # print('Total tasks: {}'.format(len(tasks)))
        print('Task sent: {}'.format(sent_counter))





