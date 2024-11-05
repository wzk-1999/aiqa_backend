import json

from django.db import transaction
from django.db.models import Q

from chatRobot.models import AIQAMessage


class mysqlUtils:

    @staticmethod
    def get_messages(user_id, session_id, count=10):
        # Query the most recent messages for the given user and session, ordered by create_time in descending order
        messages = AIQAMessage.objects.filter(user_id=user_id, session_id=session_id) \
            .order_by('-create_time')[:count] \
            .values('user_id', 'session_id', 'message_id', 'type', 'content', 'is_thumb_up', 'is_thumb_down', 'reflect_reason','quotes')

        # Convert the queryset to a list of dictionaries and handle the quotes field to restore it to an array
        result = []
        for message in messages:
            message_dict = dict(message)
            if message_dict['quotes']:
                message_dict['quotes'] = message_dict['quotes'].split('|||')
            result.append(message_dict)

        # Reverse the list to match the original order (since we sliced it in descending order)
        return result[::-1]

    @staticmethod
    def store_message(user_id, session_id,message_id, content, message_type,quotes=None):
        # 检查数据库中是否已存在具有相同 user_id, session_id, message_id 的消息
        existing_message = AIQAMessage.objects.filter(
            Q(user_id=user_id) &
            Q(session_id=session_id) &
            Q(message_id=message_id)
        ).first()

        if existing_message:
            # 如果存在，直接返回 message_id
            return existing_message.message_id
            # Create and save the message using the provided parameters

        if quotes is not None and isinstance(quotes, list):
            quotes_str = "|||".join(quotes)
        else:
            quotes_str = quotes

        message = AIQAMessage(
            user_id=user_id,
            session_id=session_id,
            message_id=message_id,
            type=message_type,
            content=content,
            quotes = quotes_str
        )

        # Save the message in the database
        message.save()

        # Return the saved message_id if needed
        return message_id

    @staticmethod
    def get_all_messages_for_ai(user_id, session_id):
        # Query all messages for the given user and session ordered by create_time in ascending order
        messages = AIQAMessage.objects.filter(user_id=user_id, session_id=session_id) \
            .order_by('create_time') \
            .values('type', 'content')  # Only select the 'type' and 'content' fields

        # Format the messages into a list of dictionaries for AI
        messages_for_ai = [{"role": message["type"], "content": message["content"]} for message in messages]

        return messages_for_ai

    @staticmethod
    def update_like_status(user_id, session_id, message_id, is_liked):
        try:
            with transaction.atomic():
                message = AIQAMessage.objects.get(user_id=user_id, session_id=session_id, message_id=message_id)
                message.is_thumb_up = is_liked
                message.save()
            return True
        except AIQAMessage.DoesNotExist:
            return False

    @staticmethod
    def update_dislike_status(user_id, session_id, message_id, is_disliked):
        try:
            with transaction.atomic():
                message = AIQAMessage.objects.get(user_id=user_id, session_id=session_id, message_id=message_id)
                message.is_thumb_down = is_disliked
                message.save()
            return True
        except AIQAMessage.DoesNotExist:
            return False