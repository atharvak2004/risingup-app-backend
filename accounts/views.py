# accounts/api_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from accounts.models import User
from .serializers import StudentCreateSerializer
from rest_framework.permissions import IsAuthenticated

class CreateStudentView(APIView):
    """
    POST /api/accounts/create-student/

    Only SUPERADMIN or SCHOOL_ADMIN can create students.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        # Only allow specific roles
        if user.role not in [User.Role.SUPERADMIN, User.Role.SCHOOL_ADMIN]:
            return Response(
                {"detail": "You are not allowed to create students."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = StudentCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        new_user = serializer.save()

        return Response(
            {
                "id": new_user.id,
                "username": new_user.username,
                "role": new_user.role,
                "school_id": new_user.school_id,
            },
            status=status.HTTP_201_CREATED,
        )


# accounts/views.py

class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Student Details
        grade_name = None
        section_name = None
        admission_no = None

        if hasattr(user, "student_profile"):
            grade = user.student_profile.grade
            section = user.student_profile.section

            grade_name = grade.name if grade else None
            section_name = section.name if section else None
            admission_no = user.student_profile.admission_no

        # School name
        school_name = user.school.name if user.school else None

        return Response({
            "id": user.id,
            "username": user.username,
            "full_name": user.get_full_name(),
            "email": user.email,
            "role": user.role,
            "school_id": user.school.id if user.school else None,
            "school_name": school_name,

            # Student profile fields
            "grade_name": grade_name,
            "section_name": section_name,
            "admission_no": admission_no,

            # flags
            "is_first_login": False,
        })
