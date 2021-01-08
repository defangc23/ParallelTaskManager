# Parallel Task Manager



## Deployment



### Docker-RabbitMQ 组件部署 

1. 拉取镜像： `docker pull rabbitmq:3.8.3-management`

2. 启动容器(消息持久化):   
                                        

   ```bash
    docker run --hostname guardstrike_mq \
               --restart=always \
               -p 5672:5672 -p 15672:15672 \
               -e RABBITMQ_DEFAULT_USER=guardstrike \
               -e RABBITMQ_DEFAULT_PASS=iiisct \
               -v /data/docker/public/rabbitmq/:/var/lib/rabbitmq/ \
               --name rabbitmq -d rabbitmq:3.8.3-management 
   ```


   ​    

3. 进入容器:    `docker exec -it rabbitmq bash`

4. 删除容器： `docker rm -f rabbitmq`





### Docker-Redis 组件部署

1. 拉取镜像：`docker pull redis`

2. 启动容器(数据持久化)：

   ```bash
   docker run --hostname guardstrike_redis \
              --restart=always \
              -p 6379:6379 \
              -v /data/docker/public/redis/data:/data \
              --name redis \
              -d redis redis-server --appendonly yes
   ```

   

### 并行框架部署

1. 安装 Nvidia-Docker

2. 拉取环境镜像: docker pull eum814/deep_env:latest

3. 编辑启动配置文件 launch_conf.json 例如：

   ```json
   {
       "Worker_List": {
           "0": {
               "OCR_0": 1
           },
           "1": {
               "OCR_1": 1
           },
           "2": {
               "OCR_2": 1
           },
           "3": {
               "OCR_3": 1
           }
       },
       "MQ_Config": {
           "rmq_host": "172.16.124.75",
           "rmq_port": 5672,
           "vhost": "/",
           "username": "guardstrike",
           "password": "iiisct",
           "rest_port": 15672,
           "retry_times": 3
       },
       "Redis_Config": {
           "redis_host": "172.16.124.75",
           "redis_port": 6379,
           "db_index": 0,
           "retry_times": 3
       }
   }
   ```

   其中包括  Worker_List , MQ_Config, Redis_Config

   Worker_List 中, 第一个key "0" 代表 gpu index; 第二个key "OCR_0" 代表worker信息, 其中OCR为worker监听的队列名, 0代表worker的id; 最后的value值代表worker是否激活, 1为启动, 0为停止.

   MQ_Config 中, 主要储存worker连接队列所使用的信息, 其中"rmq_host"为rabbitmq所部署在的host ip. 

   Redis_Config中包括了redis server的信息

   需注意worker_inference文件夹中对其调用的algo_lib库的路径进行修改.

4. 编辑launch_conf.json激活worker后用docker启动:

   ```bash
   docker run -d --name fang_worker \
           -v /:/mnt \
           -w /mnt/media/users/fangcheng/remote_deploy/ParallelTaskManager \
           --gpus all \
           eum814/deep_env:latest python main.py
   ```

5. (Demo) 自动发送任务脚本sender.py, 代码内部编辑任务文件夹路径和队列名后用docker启动:

   ```bash
   docker run -d --name fang_sender \
           -v /:/mnt \
           -w /mnt/media/users/fangcheng/remote_deploy/ParallelTaskManager \
           eum814/deep_env:latest python sender.py
   ```

6. 当队列任务清零并且从log中发现worker已经没有在处理任务时，进入launch_conf.json后将每个worker的激活状态置零.

   `docker container prune` 清理退出的容器



####  调试

docker ssh 内部环境debug:

1.  开启 screen 

2. ```bash
   docker run -it --rm --gpus all -v /:/mnt -p 10000:22 eum814/deep_env:latest bash
   ```

3.  docker 内部执行 `/etc/init.d/ssh restart`

4. 挂起 screen 