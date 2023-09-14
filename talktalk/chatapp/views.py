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
import json,math,logging

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
        logging.exception('Exceptions Occured is {}'.format(e))
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
        logging.exception('Exceptions Occured is {}'.format(e))

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
            logging.exception('Exceptions Occured is {}'.format(e))
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
            final_data=User.objects.filter(q).annotate(status=Value('Online')).values('id','username','status')
            return response_generator(status.HTTP_200_OK,final_data)

        except Exception as e:
            logging.exception('Exceptions Occured is {}'.format(e))
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
        logging.exception('Exceptions Occured is {}'.format(e))
        return response_generator(status.HTTP_500_INTERNAL_SERVER_ERROR,'Internal Server Error')
    


class UserS:

    def __init__(self):
        #considering the location of json file is static and known.
        self.final_user_data=dict()
        with open('talktalk/users.json','r') as f:
            data=json.load(f)

        for usr_data in data['users']:
            self.final_user_data[usr_data['id']]={}
            self.final_user_data[usr_data['id']]['user_id']=usr_data['id']
            self.final_user_data[usr_data['id']]['age']=usr_data['age']
            self.final_user_data[usr_data['id']]['name']=usr_data['name']
            self.final_user_data[usr_data['id']]['interests']=usr_data['interests']

users=UserS()


#currently calclating matching score based on only interests.
def similarity_check(user1,user2):
    try:
        numerator=0
        for interest in user1.get('interests'):
            numerator+=int(user1['interests'].get(interest,0))*int(user2['interests'].get(interest,0))
        mod_user1=math.sqrt(sum(x**2 for x in user1.get('interests',0).values()))
        mod_user2=math.sqrt(sum(x**2 for x in user1.get('interests',0).values()))
        denominator=(mod_user1*mod_user2)
        score=round((numerator/denominator),8)
        # logging.exception(score)
        return score
    except Exception as e:
        logging.exception('Exceptions Occured is {}'.format(e))


@api_view(['get'])
def friendrecommender(request,pk):
    try:
        similarity_score=[]
        users_data=users.final_user_data
        try:
            current_user=users_data[pk]
        # if not current_user:
        except:
            return response_generator(status.HTTP_400_BAD_REQUEST,'Invalid User id Given')
        for user_id in users_data:
            if user_id!=pk:
                cos_score=similarity_check(current_user,users_data[user_id])
                similarity_score.append((cos_score,users_data[user_id]['user_id']))

        similarity_score.sort(key=lambda x:x[0])
        top_5_frnds=[]
        for score_data in similarity_score[-6:]:
            top_5_frnds.append(users_data[score_data[1]])
        # top_5_frnds.append(users_data[pk])
        return response_generator(status.HTTP_200_OK,top_5_frnds)
    
    except Exception as e:
        logging.exception('Exceptions Occured is {}'.format(e)) 
        return response_generator(status.HTTP_500_INTERNAL_SERVER_ERROR,'Internal Server Error')
