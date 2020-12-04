docker run -d --name fang_worker \
        -v /:/mnt \
        -w /mnt/media/users/fangcheng/remote_deploy/ParallelTaskManager \
        --gpus all \
        eum814/deep_env:latest python main.py