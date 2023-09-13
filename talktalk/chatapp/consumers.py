import json
from channels.generic.websocket import WebsocketConsumer
from channels.exceptions import DenyConnection,StopConsumer,RequestAborted
from django.db.models import Q
from django.utils import timezone
from asgiref.sync import async_to_sync
from chatapp.utils import tokenkey_expiry_check
from chatapp.models import User,Message
from chatapp.serializers import MessageSerializer


class MsgConsumer(WebsocketConsumer):

    def get_messages(self):
        q = Q(Q(sender=self.scope['sender'],receiver=self.scope['receiver'])
                        |
                Q(sender=self.scope['receiver'],receiver=self.scope['sender']))
        messages=MessageSerializer(
            Message.objects.filter(q).order_by('-timestamp')
            ,many=True).data
        return messages

    def auth_check(self,scope):
        '''

            As per mention in task doc maintained url endpoint same and 
            taking receiver name from header insted of from url.

        '''
        headers = dict(scope['headers'])
        if (b'authorization' in headers) and (b'receiver' in headers):
            _,token_key = headers[b'authorization'].decode().split()
            is_expired,token_obj=tokenkey_expiry_check(token_key)
            
            if is_expired:
                raise DenyConnection('Token Expired')
        
            scope['user']=token_obj.user
            scope['sender']=token_obj.user
            receiver_qry=User.objects.filter(
                            Q(is_online=True)
                            &
                            Q(token_expiry__gte=timezone.now()),
                            username__iexact=headers[b'receiver'].decode()
                            )

            if receiver_qry.exists():
                scope['receiver']=receiver_qry.first()
            else:
                raise DenyConnection('User Doesnot Exist or Not Online')
        else:
            raise DenyConnection('Invalid Token or Expired')

    def connect(self):
        try:
            self.auth_check(self.scope)
            self.room_name = ''.join(sorted([
                self.scope['sender'].username,
                self.scope['receiver'].username
                ]))
            self.room_group_name = f"chat_{self.room_name}"
            print(self.room_group_name)
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name, self.channel_name
            )
            self.accept()
            messages=self.get_messages()
            if messages:
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,{"type":"chat.message","msg":messages}
                )
        except DenyConnection as DC:
            print('Errors by Deny Connection ',DC)
            self.close()
        except Exception as e:
            print('Error Occured is',e)
            self.close()
            
    def receive(self, text_data=None, bytes_data=None):
        if text_data:
            msg=Message(sender=self.scope['sender'],
                        receiver=self.scope['receiver'],
                        content=text_data)
            msg.save()
        messages=self.get_messages()
        async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,{"type":"chat.message","msg":messages}
                )

    def chat_message(self,event):
        self.send(json.dumps(event['msg']))

    def disconnect(self, code):
        raise StopConsumer()
        
