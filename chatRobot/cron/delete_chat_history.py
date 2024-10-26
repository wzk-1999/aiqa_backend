from datetime import timedelta
from django.utils import timezone
import os
import django
import sys

# 将项目目录添加到 sys.path
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_dir)

project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path)

# 设置 Django 环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_site.settings')
django.setup()

from chatRobot.models import AIQAMessage


def delete_chat_history():
    three_days_ago = timezone.now() - timedelta(days=3)
    # 删除旧记录并获取删除的对象数量
    deleted_count, _ = (
    AIQAMessage.objects.filter(create_time__lt=three_days_ago).delete()
    )

    current_time = timezone.localtime(timezone.now()).strftime('%Y%m%d %H:%M:%S')
    print("-------------------------------------------------------------------")
    # 打印删除了多少行以及时间戳
    print(f"[{current_time}] chat history deleted {deleted_count} records.")
    print("-------------------------------------------------------------------")


# 调用函数来删除旧记录
delete_chat_history()