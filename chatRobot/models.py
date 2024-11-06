from django.db import models

# Create your models here.
class AIQAMessage(models.Model):
    user_id = models.CharField(max_length=100)
    session_id = models.CharField(max_length=100)
    message_id = models.CharField(max_length=100)
    quotes = models.TextField(null=True)
    quote_file=models.TextField(null=True)
    type = models.CharField(max_length=50)
    content = models.TextField()
    is_thumb_up = models.BooleanField(default=False)
    is_thumb_down = models.BooleanField(default=False)
    reflect_reason = models.TextField(blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('user_id', 'session_id', 'message_id'),)
        db_table = 'aiqa_messages'

    def __str__(self):
        return f"Message {self.message_id} in Session {self.session_id} belongs to User {self.user_id}"

class IPStatistics(models.Model):

    id = models.AutoField(primary_key=True)
    ip_address = models.GenericIPAddressField()
    if_captcha  = models.BooleanField(default=False)
    request_time = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=10,null=True)  # e.g., "GET", "POST"
    api_endpoint = models.CharField(max_length=255,null=True)  # URL of the endpoint

    class Meta:
        db_table = 'aiqa_ipStatistics'
