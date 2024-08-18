from rest_framework import permissions

from movie.models import Collection
from user.models import User


class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class IsOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class CollectionRetrievePermission(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if not obj.is_private and obj.state == Collection.CollectionState.ACCEPT:
            return True

        if request.user:
            return request.user == obj.user

        return request.user.is_superuser
