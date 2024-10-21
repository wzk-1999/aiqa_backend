# 敏感信息配置文件security.py的demo
from .settings import PASSPORT_JWT
from requests.auth import HTTPBasicAuth

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'xxx'

# # Database
# # https://docs.djangoproject.com/en/1.11/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # 数据库引擎
        'NAME': 'xxx',  # 数据的库名，事先要创建之
        'HOST': '127.0.0.1',  # 主机
        'PORT': '3306',  # 数据库使用的端口
        'USER': 'xxx',  # 数据库用户名
        'PASSWORD': 'xxx',  # 密码
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES';",  # SET foreign_key_checks = 0;
            'charset': 'utf8mb4'
        },
        'TEST': {
            'NAME': 'xxx',  # unit test database
            'CHARSET': 'utf8mb4'
        },
    },
}

# 第三方应用登录认证敏感信息
THIRD_PARTY_APP_AUTH_SECURITY = {
    # 科技云通行证
    'SCIENCE_CLOUD': {
        'client_id': 0,
        'client_secret': 'xxx',
    },
}

# 邮箱配置
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True  # 是否使用TLS安全传输协议
# EMAIL_PORT = 25
EMAIL_HOST = 'xxx'
EMAIL_HOST_USER = 'xxx'
EMAIL_HOST_PASSWORD = 'xxx'

# 科技云通行证JWT认证公钥
PASSPORT_JWT['VERIFYING_KEY'] = 'xxx'

REDIS_CONFIG = {
    "HOST": "xxx",
    "PORT": 6379,
    "PASSWORD": "xxx",
}
MONGO_CONFIG = {
    "HOST": "xxx",
    "PORT": 27017,
    "USERNAME": "root",
    "PASSWORD": "xxx",
    "TABLE": "xxx",
}
# 邮件日志API
MAIL_LOG_BASEURL = "http://xxx"
# 邮件指标API
MAIL_METRIC_BASEURL = "http://xxx"
# 硬盘检测
TOOL_DISK_LOKI = "http://xxx"
# 网站群检测探针
PROBE_MAPPING = {
    "1": "http://xxx",
    "2": "http://xxx"
}

SERVICE_BACKEND = HTTPBasicAuth('xxx', 'xxx')

DINGTALKROBOT = {
    "webhook": "https://oapi.dingtalk.com/robot/send?access_token=xxx",
    "secret": "xxx"
}
MAIL_STATISTIC_CERTIFICATE = """xxx"""

MAIL_STATISTIC_URL = "xxx"

SIMPLEUI_HOME_INFO = False
SIMPLEUI_ANALYSIS = False

CORS_ALLOWED_ORIGINS = ['前端请求socket']

API_LINK_VALUE = "api link"
QWEN2_API_KEY_VALUE = "api key"

#development env: True, production env: False
DEBUG = True

CORS_ALLOWED_ORIGINS = [
    "your front-end socket",
]