### Docker-RabbitMQ 组件部署 

1. 拉取镜像： `docker pull rabbitmq:3.8.3-management`

2. chmod 777 -R /data/docker/public/rabbitmq/

3. 启动容器(消息持久化):   
                                           
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
              


      ​            

4. 进入容器:    `docker exec -it rabbitmq bash`

5. 删除容器： `docker rm -f rabbitmq`





