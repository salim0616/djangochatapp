from django.urls import path
from chatapp.views import register,login,OnlineUsers,startchat,friendrecommender

urlpatterns=[
    path('api/register/',register,name='register'),
    path('api/login/',login,name='login'),
    path('api/online-users/',OnlineUsers.as_view(),name='onlineusers'),
    path('api/chat/start/',startchat,name='startchat'),
    path('api/suggested-friends/<int:pk>',friendrecommender,name='friendrecommender'),

]