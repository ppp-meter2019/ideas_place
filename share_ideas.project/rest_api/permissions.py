from rest_framework.permissions import BasePermission


def by_method_permission_classes(overridden_permission_classes):
    def decorator(viw_method):
        def decorated_view_method(self, *args, **kwargs):
            self.permission_classes = overridden_permission_classes
            return viw_method(self, *args, **kwargs)
        return decorated_view_method
    return decorator


class IsIdeaOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return True if request.user == obj.author else False
