docker run -d --name fang_sender \
        -v /:/mnt \
        -w /mnt/media/users/fangcheng/remote_deploy/ParallelTaskManager \
        eum814/deep_env:latest python sender.py
