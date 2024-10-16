from datetime import datetime, timedelta

from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
import uuid
import json
import os
import requests
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view

from .models import IPStatistics
from .utils.generate_captcha import generate_str_captcha
from .utils.ip_related import check_ip_limit, get_client_ip
from .utils.mysqlUtils import mysqlUtils

# Synchronous view for fetching recent messages
# Define query parameters for Swagger documentation
@swagger_auto_schema(
    method='get',  # Specify the method
    manual_parameters=[
        openapi.Parameter('tmp_user_id', openapi.IN_QUERY, description="用户id,没有就随机生成", type=openapi.TYPE_STRING),
        openapi.Parameter('session_id', openapi.IN_QUERY, description="会话id,没有就随机生成", type=openapi.TYPE_STRING),
    ]
)
@api_view(['GET'])

def get_recent_messages(request):
    if check_ip_limit(request,8,50):
        tmp_user_id = request.GET.get('tmp_user_id')
        session_id = request.GET.get('session_id')

        if not tmp_user_id:
            # Generate a new session_id if it doesn't exist
            tmp_user_id = str(uuid.uuid4())
            session_id = str(uuid.uuid4())
            recent_messages = []

        else:
            if not session_id:
                session_id = str(uuid.uuid4())
                recent_messages = []
            else:
                # Fetch the recent messages from MySQL synchronously
                recent_messages = mysqlUtils.get_messages(tmp_user_id, session_id)

        return JsonResponse({
            'tmp_user_id': tmp_user_id,
            'session_id': session_id,
            'messages': recent_messages
        })
    else:
        return JsonResponse({
            'captcha': "require captcha"
        })


# # 假设这里有一个全局字典用于存储生成状态，键为用户 ID 和会话 ID 的组合，值为生成状态
# answer_generation_status = {}
#
# @swagger_auto_schema(
#     method='post',  # Specify the method for POST
#     request_body=openapi.Schema(
#         type=openapi.TYPE_OBJECT,
#         properties={
#             'session_id': openapi.Schema(type=openapi.TYPE_STRING, description='会话 ID'),
#             'tmp_user_id': openapi.Schema(type=openapi.TYPE_STRING, description='用户 id'),
#         }
#     )
# )
# @api_view(['POST'])
# def terminate_generate_answer(request):
#     try:
#         body = json.loads(request.body)
#     except json.JSONDecodeError:
#         return JsonResponse({'error': 'Invalid JSON format'}, status=400)
#
#     session_id = body.get('session_id')
#     tmp_user_id = body.get('tmp_user_id')
#     answer_generation_active = False


@swagger_auto_schema(
    method='post',  # Specify the method for POST
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'question': openapi.Schema(type=openapi.TYPE_STRING, description='用户问题'),
            'session_id': openapi.Schema(type=openapi.TYPE_STRING, description='会话 ID'),
            'tmp_user_id': openapi.Schema(type=openapi.TYPE_STRING, description='用户 id'),
            'message_id': openapi.Schema(type=openapi.TYPE_STRING, description='前端生成的消息 id'),
        }
    )
)
@api_view(['POST'])
def handle_chat_sse(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)

    question = body.get('question')
    session_id = body.get('session_id')
    tmp_user_id = body.get('tmp_user_id')
    message_id = body.get('message_id')

    if not tmp_user_id:
        return JsonResponse({'error': 'user ID is required'}, status=400)
    if not session_id:
        return JsonResponse({'error': 'Session ID is required'}, status=400)

    # Store the user's question synchronously
    mysqlUtils.store_message(tmp_user_id, session_id, message_id, question, 'user')

    # Generate the answer from the external API
    return StreamingHttpResponse(generate_answer(tmp_user_id, session_id), content_type='text/event-stream')

def generate_answer(user_id, session_id):
    chat_history = mysqlUtils.get_all_messages_for_ai(user_id, session_id)

    api_url = f"{os.getenv('API_LINK')}"
    headers = {
        "Authorization": f"Bearer {os.getenv('qwen2_API_KEY')}",  # Replace with your API key
        "Content-Type": "application/json"
    }
    data = {
        # "model": "qwen2:7b",
        "model": "qwen2.5:32b-instruct-q8_0",
        # "model": "ep-20240922110810-8njsc",
        "messages": chat_history,
        "stream": True,
        "temperature": 0.1
    }

    # qwen2: 7b 模型，用\n分隔
    # try:
    #     response = requests.post(api_url, headers=headers, json=data, stream=True)
    #     if response.status_code == 200:
    #         buffer = ""
    #         full_message = ""
    #
    #         for chunk in response.iter_lines():
    #             decoded_chunk = chunk.decode('utf-8')
    #             if decoded_chunk:
    #                 buffer += decoded_chunk
    #
    #                 while '\n' in buffer:
    #                     line, buffer = buffer.split('\n', 1)
    #
    #                     if line.startswith('data:'):
    #                         line = line[len('data:'):]
    #
    #                     try:
    #                         line_data = json.loads(line)
    #                         if 'choices' in line_data and line_data['choices']:
    #                             chunk_message = line_data['choices'][0]['delta'].get('content', '')
    #                             full_message += chunk_message
    #
    #                             yield f"data: {json.dumps({'message': chunk_message})}\n\n"
    #
    #                             if line_data['choices'][0].get('finish_reason') == 'stop':
    #                                 mysqlUtils.store_message(user_id, session_id, str(uuid.uuid4()), full_message,
    #                                                          'assistant')
    #                                 return  # End the generator when the stream finishes
    #                     except json.JSONDecodeError:
    #                         continue
    #     else:
    #         yield f"data: {json.dumps({'error': 'Failed to get a valid response.'})}\n\n"
    # except requests.RequestException as e:
    #     yield f"data: {json.dumps({'error': f'Error connecting to API: {e}'})}\n\n"

    # qwen2.5:32b-instruct-q8_0 模型，用''分割
    try:
        response = requests.post(api_url, headers=headers, json=data, stream=True)
        if response.status_code == 200:
            full_message = ""
            messages_id = str(uuid.uuid4());
            for chunk in response.iter_lines():
                decoded_chunk = chunk.decode('utf-8')
                if decoded_chunk:
                    if decoded_chunk.startswith('data:'):
                        decoded_chunk = decoded_chunk[len('data:'):]
                    try:
                        line_data = json.loads(decoded_chunk)
                        if 'choices' in line_data and line_data['choices']:
                            chunk_message = line_data['choices'][0]['delta'].get('content', '')
                            full_message += chunk_message
                            try:
                                yield f"data: {json.dumps({'message': chunk_message})}\n\n"
                            except:
                                print("ConnectionError, didn't send message"+session_id)
                                mysqlUtils.store_message(user_id, session_id, messages_id, full_message,
                                                         'assistant')

                            if line_data['choices'][0].get('finish_reason') == 'stop':
                                mysqlUtils.store_message(user_id, session_id, messages_id, full_message,
                                                         'assistant')
                                # try:
                                yield f"data: {json.dumps({'messages_id': messages_id})}\n\n"
                                # except requests.exceptions.ConnectionError:
                                #     print("ConnectionError, didn't send message")
                                return # End the generator when the stream finishes

                    except json.JSONDecodeError:
                        continue
        else:
            yield f"data: {json.dumps({'error': 'Failed to get a valid response.'})}\n\n"
            return
    except requests.RequestException as e:
        yield f"data: {json.dumps({'error': f'Error connecting to API: {e}'})}\n\n"
        return


@api_view(['GET'])
@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({'csrfToken': request.META.get('CSRF_COOKIE')})

@api_view(['GET'])
def check_captcha_required(request):
    if check_ip_limit(request, 8, 3):
        return JsonResponse({'captcha_required': False})
    else:
        return JsonResponse({'captcha_required': True})

captcha_memory = {}
@api_view(['GET'])
@require_http_methods(["GET"])
def get_captcha(request, user_id):
    # user_id=request.path_info.split('/')[4]
    img, captcha = generate_str_captcha()
    # 将验证码存储在内存中，使用 user_id 构造键
    # 设置一分钟后过期
    expiration_time = datetime.now() + timedelta(minutes=1)

    captcha_memory[user_id + "_captcha"] = (captcha,expiration_time)
    # return HttpResponse(img,content_type='image/png')
    return HttpResponse(img)

@swagger_auto_schema(
    method='post',  # Specify the method for POST
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_STRING, description='用户id'),
            'captcha_input': openapi.Schema(type=openapi.TYPE_STRING, description='用户输入的验证码'),
        }
    )
)
@api_view(['POST'])

def verify_captcha(request):
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        user_captcha = data.get('captcha_input')
        stored_captcha_key = user_id + "_captcha"
        if stored_captcha_key in captcha_memory:
            stored_captcha, expiration_time = captcha_memory[stored_captcha_key]
            if datetime.now() <= expiration_time and user_captcha == stored_captcha:
                # 验证成功，从内存中删除该验证码
                del captcha_memory[stored_captcha_key]

                user_ip=get_client_ip(request)
                # Get the most recent record with the same IP address
                latest_request = IPStatistics.objects.filter(ip_address=user_ip).order_by('-request_time').first()

                if latest_request:
                    latest_request.if_captcha = True  # Update the if_captcha field to True
                    latest_request.save()  # Save the changes
                return JsonResponse({'message': '验证通过','result':True})
            else:
                del captcha_memory[stored_captcha_key]
        return JsonResponse({'message': '输入错误或超时，请重新获取后再次验证','result':False})
    except json.JSONDecodeError:
        return JsonResponse({'message': '无效的请求格式','result':False}, status=400)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_STRING, description='用户id'),
            'session_id': openapi.Schema(type=openapi.TYPE_STRING, description='会话id'),
            'message_id': openapi.Schema(type=openapi.TYPE_STRING, description='消息id'),
            'isLiked': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否点赞，布尔值'),
        }
    )
)
@api_view(['POST'])
def handle_like(request):
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        message_id = data.get('message_id')
        is_liked = data.get('isLiked')
        if message_id and is_liked is not None:
            # Update the database or Redis here...
            if mysqlUtils.update_like_status(user_id,session_id, message_id, is_liked):
                # Respond with success
                return JsonResponse({'message': 'like status changed successfully'}, status=200)
        else:
            return JsonResponse({'error':'error in updating like status'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'message': '无效的请求格式'}, status=400)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_STRING, description='用户id'),
            'session_id': openapi.Schema(type=openapi.TYPE_STRING, description='会话id'),
            'message_id': openapi.Schema(type=openapi.TYPE_STRING, description='消息id'),
            'isDisLiked': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否踩，布尔值'),
        }
    )
)
@api_view(['POST'])
def handle_dislike(request):
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        message_id = data.get('message_id')
        is_disliked = data.get('isDisLiked')
        if message_id and is_disliked is not None:
            # Update the database or Redis here...
            if mysqlUtils.update_dislike_status(user_id,session_id, message_id, is_disliked):
                # Respond with success
                return JsonResponse({'message': 'like status changed successfully'}, status=200)
        else:
            return JsonResponse({'error':'error in updating like status'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'message': '无效的请求格式'}, status=400)