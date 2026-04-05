# accounts/permissions.py
from rest_framework.permissions import BasePermission
from .models import User


class IsSuperAdminOrSchoolAdmin(BasePermission):
    """
    Allows access only to SUPERADMIN or SCHOOL_ADMIN users.
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) in [User.Role.SUPERADMIN, User.Role.SCHOOL_ADMIN]
        )


class IsStudent(BasePermission):
    """
    Allows access only to STUDENT role.
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) == User.Role.STUDENT
        )


class IsStaff(BasePermission):
    """
    Allows access only to STAFF role.
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) == User.Role.STAFF
        )
        
class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.SUPERADMIN
        )
