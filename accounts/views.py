# accounts/api_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.models import User
from accounts.permissions import IsSuperAdminOrSchoolAdmin
from .serializers import SchoolLoginSerializer, StudentCSVUploadSerializer, StudentCreateSerializer, StudentBulkCreateSerializer, StudentLoginSerializer, StudentProfileUpdateSerializer

from accounts.utils import generate_password
from accounts.email_utils import send_student_credentials
class CreateStudentView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdminOrSchoolAdmin]

    def post(self, request):
        serializer = StudentCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "school_id": user.school_id,
            },
            status=status.HTTP_201_CREATED,
        )
class AddStudentBulkAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrSchoolAdmin]

    def post(self, request):
        serializer = StudentBulkCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        result = serializer.save()
        return Response(result, status=status.HTTP_201_CREATED)

class AddStudentCSVAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrSchoolAdmin]

    def post(self, request):
        serializer = StudentCSVUploadSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        result = serializer.save()
        return Response(result, status=status.HTTP_201_CREATED)


class ForcePasswordResetAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        new_password = request.data.get("new_password")

        if not user.is_first_login:
            return Response(
                {"detail": "Password reset not required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not new_password or len(new_password) < 8:
            return Response(
                {"detail": "Password must be at least 8 characters"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.is_first_login = False
        user.save()

        return Response({"message": "Password updated successfully"})
    
class AdminResetStudentPasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, student_id):
        student = User.objects.get(id=student_id, role=User.Role.STUDENT)

        temp_password = generate_password()
        student.set_password(temp_password)
        student.is_first_login = True
        student.save()

        send_student_credentials(
            email=student.email,
            username=student.username,
            password=temp_password,
        )

        return Response({"message": "Password reset & emailed"})

class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Student details
        grade_name = None
        section_name = None
        admission_no = None

        if hasattr(user, "student_profile"):
            grade = user.student_profile.grade
            section = user.student_profile.section
            grade_name = grade.name if grade else None
            section_name = section.name if section else None
            admission_no = user.student_profile.admission_no

        # Staff details
        staff_designation = None
        staff_grade_name = None
        staff_section_name = None

        if hasattr(user, "staff_profile"):
            staff_designation = user.staff_profile.designation
            s_grade = user.staff_profile.assigned_grade
            s_section = user.staff_profile.assigned_section
            staff_grade_name = s_grade.name if s_grade else None
            staff_section_name = s_section.name if s_section else None

        # School name
        school_name = user.school.name if user.school else None

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "full_name": user.get_full_name(),
                "email": user.email,
                "role": user.role,
                "phone": user.phone,
                "school_id": user.school.id if user.school else None,
                "school_name": school_name,
                # Student profile fields
                "grade_name": grade_name,
                "section_name": section_name,
                "admission_no": admission_no,
                # Staff profile fields
                "staff_designation": staff_designation,
                "staff_grade_name": staff_grade_name,
                "staff_section_name": staff_section_name,
                # flags
                "is_first_login": user.is_first_login,
            }
        )

from rest_framework_simplejwt.tokens import RefreshToken
class SchoolLoginView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = SchoolLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
            }
        })
        
class StudentLoginView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = StudentLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        # Student profile
        grade_name = None
        section_name = None
        admission_no = None

        if hasattr(user, "student_profile"):
            grade = user.student_profile.grade
            section = user.student_profile.section

            grade_name = grade.name if grade else None
            section_name = section.name if section else None
            admission_no = user.student_profile.admission_no

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.get_full_name(),
                "email": user.email,
                "role": user.role,
                "phone": user.phone,
                "school_id": user.school.id if user.school else None,
                "school_name": user.school.name if user.school else None,

                # Student fields
                "grade_name": grade_name,
                "section_name": section_name,
                "admission_no": admission_no,

                # flags
                "is_first_login": user.is_first_login,
            }
        })
        
class StudentProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role != User.Role.STUDENT:
            return Response(
                {"detail": "Only students can access this"},
                status=status.HTTP_403_FORBIDDEN,
            )

        profile = user.student_profile

        return Response({
            "id": user.id,
            "username": user.username,
            "full_name": user.get_full_name(),
            "email": user.email,
            "phone": user.phone,

            "school_id": user.school.id if user.school else None,
            "school_name": user.school.name if user.school else None,

            "grade_id": profile.grade.id if profile.grade else None,
            "grade_name": profile.grade.name if profile.grade else None,

            "section_id": profile.section.id if profile.section else None,
            "section_name": profile.section.name if profile.section else None,

            "admission_no": profile.admission_no,

            "is_first_login": user.is_first_login,
        })

class StudentProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user

        if user.role != User.Role.STUDENT:
            return Response(
                {"detail": "Only students can update profile"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = StudentProfileUpdateSerializer(
            user,
            data=request.data,
            partial=True  # allows PATCH-like behavior
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "Profile updated successfully",
            "data": serializer.data
        })
