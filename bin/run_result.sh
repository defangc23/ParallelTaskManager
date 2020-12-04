docker run -d --name fang_result \
        -v /:/mnt \
        -w /mnt/media/users/fangcheng/remote_deploy/ParallelTaskManager/utils \
        eum814/deep_env:latest python exportCSV.py