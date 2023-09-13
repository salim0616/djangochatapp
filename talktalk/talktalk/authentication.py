from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from chatapp.utils import token_expiry_check


class ChatappAuthenticate(TokenAuthentication):

    keyword='Bearer'
    model=Token

    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise AuthenticationFailed('Invalid token.')
        
        if not token.user.is_active:
            raise AuthenticationFailed("User is not active")

        is_expired = token_expiry_check(token)
        if is_expired:
            raise AuthenticationFailed("The Token is expired")
        
        return (token.user, token)
