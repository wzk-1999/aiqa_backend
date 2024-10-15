cp /home/uwsgi/aiqa/00_script/aiqabackend.service /usr/lib/systemd/system/ -f
systemctl daemon-reload
systemctl enable aiqabackend
