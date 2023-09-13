from django.urls import path
from chatapp.consumers import MsgConsumer

# just to distinguish ws and normal http request from url endpoint

websocket_urlpatterns=[
    path('ws/api/chat/send/',MsgConsumer.as_asgi()),
]