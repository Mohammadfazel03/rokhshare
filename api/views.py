from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from django.core.mail import EmailMessage
from user.serializers import RegisterUserSerializer
from django.template.loader import render_to_string


# Create your views here.
class AuthViewSet(ViewSet):

    @action(methods=['POST'], detail=False, permission_classes=[AllowAny])
    def register(self, request):
        user_serializer = RegisterUserSerializer(data=request.data)
        if user_serializer.is_valid(raise_exception=True):
            user, user_token = user_serializer.save()
            current_site = get_current_site(request)
            user.get_full_name()
            message = render_to_string('active_email.html', {
                'user': user, 'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': user_token.token,
            })
            # Sending activation link in terminal
            # user.email_user(subject, message)
            mail_subject = 'Activate your account.'
            email = EmailMessage(mail_subject, message, to=[user.email])
            email.send()

        return Response("created", status=status.HTTP_201_CREATED)
