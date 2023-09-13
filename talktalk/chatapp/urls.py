from django.urls import path
from chatapp.views import register,login,OnlineUsers,startchat

urlpatterns=[
    path('api/register/',register,name='register'),
    path('api/login/',login,name='login'),
    path('api/online-users/',OnlineUsers.as_view(),name='onlineusers'),
    path('api/chat/start/',startchat,name='startchat'),
    

]