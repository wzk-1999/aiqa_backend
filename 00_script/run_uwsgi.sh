#!/bin/bash
API_LINK=${API_LINK}
qwen2_API_KEY=${qwen2_API_KEY}
uwsgi --ini /home/uwsgi/aiqa/00_script/uwsgi.ini
