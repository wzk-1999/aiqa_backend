import re

from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
import uuid
import json
import requests
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view

from django_site.security import API_LINK_VALUE, QWEN2_API_KEY_VALUE, API_LINK_GET_CONVERSATION_ID
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
    if check_ip_limit(request,8,100):
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

    api_url = f"{API_LINK_VALUE}"
    headers = {
        "Authorization": f"Bearer {QWEN2_API_KEY_VALUE}",  # Replace with your API key
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

# 新api 开始

# Synchronous view for fetching recent messages
# Define query parameters for Swagger documentation
@swagger_auto_schema(
    method='get',  # Specify the method
    manual_parameters=[
        openapi.Parameter('tmp_user_id', openapi.IN_QUERY, description="用户id,没有就随机生成", type=openapi.TYPE_STRING),
        openapi.Parameter('session_id', openapi.IN_QUERY, description="会话id,没有就由api生成", type=openapi.TYPE_STRING),
    ]
)
@api_view(['GET'])

def get_recent_messages_new(request):
    if check_ip_limit(request,8,100):
        tmp_user_id = request.GET.get('tmp_user_id')
        session_id = request.GET.get('session_id')

        if not tmp_user_id:
            # Generate a new session_id if it doesn't exist
            tmp_user_id = str(uuid.uuid4())
            api_url = f"{API_LINK_GET_CONVERSATION_ID}?user_id={tmp_user_id}"
            headers = {'Authorization': f'Bearer {QWEN2_API_KEY_VALUE}'}
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                data = json.loads(response.text)
                session_id = data.get('data', {}).get('id')
                if not session_id:
                    raise ValueError("Failed to obtain a valid session_id from the API.")
            else:
                raise ValueError(f"API request failed with status code {response.status_code}.")
            recent_messages = []


        else:
                if not session_id:
                    api_url = f"{API_LINK_GET_CONVERSATION_ID}?user_id={tmp_user_id}"
                    headers = {'Authorization': f'Bearer {QWEN2_API_KEY_VALUE}'}
                    response = requests.get(api_url, headers=headers)
                    if response.status_code == 200:
                        data = json.loads(response.text)
                        session_id = data.get('data', {}).get('id')
                        if not session_id:
                            raise ValueError("Failed to obtain a valid session_id from the API.")
                    else:
                        raise ValueError(f"API request failed with status code {response.status_code}.")
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
def handle_chat_sse_new(request):
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
    return StreamingHttpResponse(generate_answer_new(tmp_user_id, session_id), content_type='text/event-stream')

def generate_answer_new(user_id, session_id):
    chat_history = mysqlUtils.get_all_messages_for_ai(user_id, session_id)

    api_url = f"{API_LINK_VALUE}"
    headers = {
        "Authorization": f"Bearer {QWEN2_API_KEY_VALUE}",  # Replace with your API key
    }
    data = {
        "conversation_id": session_id,
        "messages": chat_history,
        "quote": True
    }

    try:
        response = requests.post(api_url, headers=headers, json=data, stream=True)
        if response.status_code == 200:
            answer = ""
            messages_id = str(uuid.uuid4())
            for chunk in response.iter_lines():
                if chunk:
                    try:
                        if chunk.startswith(b'data:'):
                            chunk = chunk[len(b'data:'):].decode('utf-8')
                        line_data = json.loads(chunk)
                        if line_data.get('retcode') == 0:
                            data_content = line_data['data']
                            if isinstance(data_content, dict) and 'answer' in data_content and data_content['reference']:
                                answer = data_content['answer']
                                # 提取answer里##0$$这种格式的信息并处理
                                processed_info = []
                                quote_files=[]
                                pattern = re.compile(r'##(\d+)\$\$')
                                matches = pattern.findall(answer)
                                for index_str in matches:
                                    try:
                                        index = int(index_str)
                                        content_with_weight = data_content['reference']['chunks'][index]['content_with_weight']
                                        quote_file = data_content['reference']['chunks'][index]['doc_name'].split("/")[-1].split(".")[0]
                                        processed_info.append(content_with_weight)
                                        quote_files.append(quote_file)
                                    except (ValueError, KeyError):
                                        continue
                                mysqlUtils.store_message(user_id, session_id, messages_id, answer, 'assistant',processed_info,quote_files)
                                yield f"data: {json.dumps({'message': answer, 'quote': processed_info,'quote_file':quote_files})}\n\n"
                                yield f"data: {json.dumps({'messages_id': messages_id})}\n\n"
                                return

                            elif isinstance(data_content, dict) and 'answer' in data_content:
                                answer = data_content['answer']
                                yield f"data: {json.dumps({'message': answer})}\n\n"
                    except json.JSONDecodeError:
                        continue
        else:
            yield f"data: {json.dumps({'error': 'Failed to get a valid response.'})}\n\n"
            return
    except requests.RequestException as e:
        # In case of connection error, store the message if there is any accumulated content
        if answer:
            mysqlUtils.store_message(user_id, session_id, messages_id, answer, 'assistant')
        yield f"data: {json.dumps({'error': f'Error connecting to API: {e}'})}\n\n"
        return

# 新api 结束


@api_view(['GET'])
@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({'csrfToken': request.META.get('CSRF_COOKIE')})

@api_view(['GET'])
def check_captcha_required(request):
    if check_ip_limit(request, 8, 50):
        return JsonResponse({'captcha_required': False})
    else:
        return JsonResponse({'captcha_required': True})


@api_view(['GET'])
@require_http_methods(["GET"])
def get_captcha(request, user_id):
    img, captcha = generate_str_captcha()

    # 直接将验证码字符串存储到 session
    request.session['captcha'] = captcha

    return HttpResponse(img, content_type='image/png')


@swagger_auto_schema(
    method='post',
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
        input_captcha = data.get('captcha_input')

        # 从 session 获取存储的验证码
        stored_captcha = request.session.get('captcha')

        # 验证验证码
        if stored_captcha and stored_captcha == input_captcha.lower():
            user_ip = get_client_ip(request)
            # 获取最近的 IP 请求记录
            latest_request = IPStatistics.objects.filter(ip_address=user_ip).order_by('-request_time').first()

            if latest_request:
                latest_request.if_captcha = True  # 更新 if_captcha 字段为 True
                latest_request.save()  # 保存修改
            return JsonResponse({'message': '验证通过', 'result': True})
        else:
            return JsonResponse({'message': '验证码错误或已过期，请使用新验证码再次验证', 'result': False})
    except json.JSONDecodeError:
        return JsonResponse({'message': '无效的请求格式', 'result': False}, status=400)


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