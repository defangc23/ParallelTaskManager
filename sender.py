import json, glob
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
    TASK_FOLDER = '/mnt/media/users/fangcheng/test_img/OCR-POC/OCR/imgs_3000'
    QUEUE_NAME = 'OCR'

    with open(LAUNCH_CONF_PATH) as f:
        launch_conf_dict = json.load(f)
        mq_config = launch_conf_dict["MQ_Config"]

    sender = MQ_Sender(mq_config)
    tasks = glob.glob(TASK_FOLDER + '/*')
    sent_counter = 0
    for t in tasks:
        send_stat = sender.send(QUEUE_NAME, {"img_path":t, "ground_truth":""})
        if send_stat:
            sent_counter += 1
    sender.release()
    print('Total tasks: {}'.format(len(tasks)))
    print('Task sent: {}'.format(sent_counter))




