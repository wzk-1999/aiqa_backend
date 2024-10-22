from django.urls import path
from . import views

urlpatterns = [
    path('inquiry/', views.get_recent_messages_new, name='recent_messages'),
    path('chat/stream/', views.handle_chat_sse_new, name='chat_stream'),
    path('get_csrf_token/', views.get_csrf_token, name='get_csrf_token'),
    path('get_captcha/<user_id>', views.get_captcha, name='get_captcha'),
    path('verify_captcha/', views.verify_captcha, name='verify_captcha'),
    path('message/like/', views.handle_like, name='handle_like'),
    path('message/dislike/', views.handle_dislike, name='handle_dislike'),
    path('check/captcha/necessity/', views.check_captcha_required, name='check_captcha_necessity'),
]