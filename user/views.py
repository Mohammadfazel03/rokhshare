from django.db.models import Q, Model
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

from user.models import User, UserToken
from django.utils import timezone


# Create your views here.
def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None:
        try:
            user_token = UserToken.objects.get(
                Q(token=token) & Q(user=user) & Q(expire_date__gt=timezone.now()))
            user.is_active = True
            user.save()
            return HttpResponse('Thank you for your email confirmation. Now you can login your account.')
        except UserToken.DoesNotExist:
            return HttpResponse('Activation link is invalid!')
    else:
        return HttpResponse('Activation link is invalid!')
