from rest_framework import permissions


class IsModerator(permissions.BasePermission):
    """Разрешение только для модераторов"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name='moderators').exists()


class IsOwner(permissions.BasePermission):
    """Разрешение только для владельца объекта"""

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsOwnerOrModerator(permissions.BasePermission):
    """Разрешение для владельца объекта или модератора"""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        is_moderator = request.user.groups.filter(name='moderators').exists()
        is_owner = obj.owner == request.user
        return is_moderator or is_owner


class CanCreateCourseLesson(permissions.BasePermission):
    """Модераторы НЕ могут создавать курсы и уроки"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        # Модераторы не могут создавать
        if request.user.groups.filter(name='moderators').exists():
            return False
        return True


class CanDeleteCourseLesson(permissions.BasePermission):
    """Модераторы НЕ могут удалять курсы и уроки"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        # Модераторы не могут удалять
        if request.user.groups.filter(name='moderators').exists():
            return False
        return True

    def has_object_permission(self, request, view, obj):
        # Модераторы не могут удалять даже чужие объекты
        if request.user.groups.filter(name='moderators').exists():
            return False
        # Владелец может удалять свой объект
        return obj.owner == request.user