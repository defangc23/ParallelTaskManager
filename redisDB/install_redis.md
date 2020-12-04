### Docker-Redis 部署

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

   

