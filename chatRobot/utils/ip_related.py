from datetime import timedelta

from django.utils import timezone

from chatRobot.models import IPStatistics


def get_client_ip(request):
    # 考虑一些特殊情况，比如 CloudFlare 的头信息
    cloudflare_ip_header = request.META.get('HTTP_CF_CONNECTING_IP')
    if cloudflare_ip_header:
        return cloudflare_ip_header
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # 如果存在多个代理，取第一个 IP
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def check_ip_limit(request, hours=8, limit=10):
    client_ip = get_client_ip(request)
    if not client_ip:
        return False

    time_threshold = timezone.now() - timedelta(hours=hours)
    method = request.method
    api_endpoint = request.path

    # Count the number of records for the IP address in the given time frame
    count = IPStatistics.objects.filter(ip_address=client_ip, request_time__gte=time_threshold,method=method,
        api_endpoint=api_endpoint).count()+1

    # Count how many of these requests have if_captcha=True
    captcha_count = IPStatistics.objects.filter(ip_address=client_ip, request_time__gte=time_threshold,method=method,
        api_endpoint=api_endpoint,
                                                if_captcha=True).count()

    # Update the limit based on the captcha count
    new_limit = limit + limit * captcha_count

    # Always create a new record for the current request
    ip_record = IPStatistics(ip_address=client_ip,method=method,
        api_endpoint=api_endpoint)
    ip_record.save()
    # If the record was just created or if the count is below the limit
    if count < new_limit:
        return True
    else:
        # ip_record.if_captcha = True
        return False