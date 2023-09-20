from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.response import Response


def response_generator(status_code, content):
    if status_code >= 400:
        final_res = {"status": status_code, "error": content}
    else:
        final_res = {"status": status_code, "data": content}
    return Response(final_res, status=status_code)


def token_expiry_check(token_obj):
    if timezone.now() > token_obj.user.token_expiry:
        return 1
    return 0


def tokenkey_expiry_check(key):
    try:
        token = Token.objects.select_related("user").get(key=key)
    except Token.DoesNotExist:
        return 1, None
    return token_expiry_check(token), token
