from datetime import datetime,timedelta
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view,permission_classes,authentication_classes
from rest_framework import generics
from chatapp.serializers import RegisterSerializer
from rest_framework import status
from chatapp.utils import response_generator,tokenkey_expiry_check
from rest_framework.authtoken.models import Token
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from talktalk.authentication import ChatappAuthenticate
from rest_framework.permissions import AllowAny,IsAuthenticated
from chatapp.models import User
from django.db.models import Q,Value


@api_view(['post'])
@permission_classes([AllowAny])
def register(request):
    try:
        registerserializer=RegisterSerializer(data=request.data)
        if not registerserializer.is_valid():
            return response_generator(status.HTTP_400_BAD_REQUEST,registerserializer.errors)
        registerserializer.save()
        return response_generator(status.HTTP_200_OK,'Successfully Registered')
        
    except Exception as e:
        print('Exceptions Occured is',e)
        return response_generator(status.HTTP_500_INTERNAL_SERVER_ERROR,'Internal Server Error')


@api_view(['post'])
@permission_classes([AllowAny])
def login(request):
    try:

        '''

            generating new token on each login request and 
            deleting the existing token for the user.

        '''
        user=authenticate(username=request.data.get('username'),
                          password=request.data.get('password'))
        if not user:
            return response_generator(status.HTTP_401_UNAUTHORIZED,'Invalid Credentials..')
        token_qry=Token.objects.filter(user=user)
        if token_qry.exists():
            token_obj=token_qry.first()
            token_obj.delete()
        login_dt=timezone.now()
        with transaction.atomic():
            token=Token.objects.create(user=user,created=login_dt)
            exp=login_dt+timedelta(minutes=settings.TOKEN_EXPIRY)
            user.last_login=timezone.now()
            user.token_expiry=exp
            user.is_online=True
            user.save()
            data={'access_key':str(token)}
            return response_generator(status.HTTP_200_OK,data)
        

    except Exception as e:
        print('Exceptions Occured is',e)
        return response_generator(status.HTTP_500_INTERNAL_SERVER_ERROR,'Internal Server Error')
    

@api_view(['post'])
def logout(request):
    try:
        token_key=request.data.get('token')
        if token_key:
            is_expiry,token_obj=tokenkey_expiry_check(token_key)
            if token_obj:
                token_obj.delete()
        return response_generator(status.HTTP_200_OK,'successfully logged out..') 


    except Exception as e:
            print('Exceptions Occured is',e)
            return response_generator(status.HTTP_500_INTERNAL_SERVER_ERROR,'Internal Server Error')
    

class OnlineUsers(generics.ListAPIView):

    authentication_classes=[ChatappAuthenticate]
    permission_classes=[IsAuthenticated]
    http_method_names=['get']
    
    def get(self,request,*args,**kwargs):
        '''
            showing all the users who were all online and whose token is not expired.
            In this current user will also be their. 
        
        '''

        try:
            '''

                Here django queries were used to give response
                insted of serializers to_representation.
                Serilizers to_representation will be used in some other api to show the awareness.
                Also using serilizer might reduce the perfomance.
            
            '''

            q=Q(is_online=True)&Q(token_expiry__gte=timezone.now())
            final_data=User.objects.filter(q).annotate(status=Value('Online')).values('username','status')
            return response_generator(status.HTTP_200_OK,final_data)

        except Exception as e:
            print('Exceptions Occured is',e)
            return response_generator(status.HTTP_500_INTERNAL_SERVER_ERROR,'Internal Server Error')
    

@api_view(['post'])
@authentication_classes([ChatappAuthenticate])
@permission_classes([IsAuthenticated])
def startchat(request):
    try:
        chat_initiated_with_user_id=request.data.get('user_id')

        q=Q(is_online=True)&Q(token_expiry__gte=timezone.now())&Q(id=chat_initiated_with_user_id)
        user_qry=User.objects.filter(q)
        if user_qry.exists():
            return response_generator(status.HTTP_200_OK,'Success')
        else:
            return response_generator(status.HTTP_400_BAD_REQUEST,'User not "Available Online" or "exists"')

    except Exception as e:
            print('Exceptions Occured is',e)
            return response_generator(status.HTTP_500_INTERNAL_SERVER_ERROR,'Internal Server Error')
    


