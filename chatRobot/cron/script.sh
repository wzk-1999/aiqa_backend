TZ=Asia/Shanghai
0 0 */3 * * /usr/bin/python3 /home/uwsgi/aiqa/chatRobot/cron/delete_ip.py >> /var/log/aiqa/cron/delete_ip.log 2>&1
0 0 */3 * * /usr/bin/python3 /home/uwsgi/aiqa/chatRobot/cron/delete_chat_history.py >> /var/log/aiqa/cron/delete_chat_history.log 2>&1
0 0 */3 * * /usr/bin/python3 /home/uwsgi/aiqa/manage.py clearsessions >> /var/log/aiqa/cron/clearsessions.log 2>&1
