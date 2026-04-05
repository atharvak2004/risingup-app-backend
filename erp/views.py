from django.utils import timezone
from django.db import models

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from django.contrib.auth import get_user_model

from accounts.models import StaffProfile, StudentProfile
from accounts.permissions import IsSuperAdminOrSchoolAdmin
from accounts.serializers import StudentCreateSerializer

from core.models import Grade, Section
from learning.models import TheoryTopic, CaseStudy, StudentCaseStudyAttempt

from .models import SchoolReferral, ContactMessage

from .serializers import (
    SchoolProfileSerializer,
    StudentListSerializer,
    StudentProgressSerializer,
    ChapterSerializer,
    TestSerializer,
    ReportSerializer,
    SchoolReferralSerializer,
    ContactMessageSerializer,
    SchoolProfileUpdateSerializer,
)

User = get_user_model()


# ----------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------

def get_school(user):
    if not user.school:
        return None
    return user.school


# ----------------------------------------------------
# ADD STUDENT
# ----------------------------------------------------
class AddStudentAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrSchoolAdmin]

    def post(self, request):

        serializer = StudentCreateSerializer(
            data=request.data,
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        new_user = serializer.save()

        return Response(
            {
                "id": new_user.id,
                "username": new_user.username,
                "role": new_user.role,
                "school": {
                    "id": new_user.school.id if new_user.school else None,
                    "name": new_user.school.name if new_user.school else None,
                },
            },
            status=status.HTTP_201_CREATED,
        )


# ----------------------------------------------------
# DELETE STUDENT
# ----------------------------------------------------
class DeleteStudentAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrSchoolAdmin]

    def delete(self, request, student_id):

        user = request.user

        try:
            student = User.objects.get(id=student_id, role="STUDENT")
        except User.DoesNotExist:
            return Response({"error": "Student not found"}, status=404)

        if user.role != User.Role.SUPERADMIN:
            if not user.school or student.school != user.school:
                return Response(
                    {"detail": "You cannot delete students from another school"},
                    status=403,
                )

        student.delete()

        return Response({"message": "Student deleted successfully"})


# ----------------------------------------------------
# STUDENT PROGRESS
# ----------------------------------------------------
class StudentProgressAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrSchoolAdmin]

    def get(self, request, student_id):

        user = request.user

        try:
            student = User.objects.get(id=student_id, role="STUDENT")
        except User.DoesNotExist:
            return Response({"detail": "Student not found"}, status=404)

        if user.role != User.Role.SUPERADMIN:
            if student.school != user.school:
                return Response(
                    {"detail": "You cannot view another school's student"},
                    status=403,
                )

        attempts = (
            StudentCaseStudyAttempt.objects
            .filter(student=student)
            .select_related("case_study")
            .order_by("-completed_at")
        )

        serializer = StudentProgressSerializer(attempts, many=True)

        return Response({
            "student": {
                "id": student.id,
                "username": student.username,
                "name": student.get_full_name()
            },
            "progress": serializer.data
        })


# ----------------------------------------------------
# CLASS PROGRESS
# ----------------------------------------------------
class ClassProgressAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrSchoolAdmin]

    def get(self, request, grade_id, section_id):

        user = request.user

        try:
            grade = Grade.objects.get(id=grade_id)
            section = Section.objects.get(id=section_id, grade=grade)
        except (Grade.DoesNotExist, Section.DoesNotExist):
            return Response({"detail": "Grade or section not found"}, status=404)

        if user.role != User.Role.SUPERADMIN:
            if grade.school != user.school:
                return Response(
                    {"detail": "You cannot view another school's class"},
                    status=403,
                )

        students = StudentProfile.objects.filter(
            grade=grade,
            section=section
        ).select_related("user")

        total_students = students.count()

        completed_students = (
            StudentCaseStudyAttempt.objects
            .filter(
                student__student_profile__grade=grade,
                student__student_profile__section=section
            )
            .values_list("student_id", flat=True)
            .distinct()
        )

        completed = completed_students.count()
        pending = total_students - completed

        completion_rate = (completed / total_students * 100) if total_students else 0

        return Response({
            "class": {
                "grade": grade.name,
                "section": section.name
            },
            "stats": {
                "total_students": total_students,
                "completed": completed,
                "pending": pending,
                "completion_rate": round(completion_rate, 2)
            }
        })


# ----------------------------------------------------
# CONTENT API
# ----------------------------------------------------
class ContentAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, grade_id):

        user = request.user

        try:
            grade = Grade.objects.get(id=grade_id)
        except Grade.DoesNotExist:
            return Response({"detail": "Grade not found"}, status=404)

        if user.school and grade.school != user.school:
            return Response(
                {"detail": "You cannot view content of another school"},
                status=403,
            )

        chapters = (
            TheoryTopic.objects
            .filter(grade=grade, parent=None)
            .select_related("service")
            .order_by("order")
        )

        tests = (
            CaseStudy.objects
            .filter(grade=grade, is_active=True)
            .select_related("service")
        )

        return Response({
            "grade": grade.name,
            "chapters": ChapterSerializer(chapters, many=True).data,
            "tests": TestSerializer(tests, many=True).data,
        })


# ----------------------------------------------------
# REPORTS API
# ----------------------------------------------------
class ReportsAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrSchoolAdmin]

    def get(self, request):

        school = request.user.school

        if not school:
            return Response({"detail": "School not linked"}, status=400)

        students = StudentProfile.objects.filter(grade__school=school)

        total_students = students.count()

        attempts = StudentCaseStudyAttempt.objects.filter(student__school=school)

        completed_tests = attempts.count()

        avg_score = attempts.aggregate(avg=models.Avg("score"))["avg"] or 0

        completion_rate = (
            (completed_tests / total_students * 100) if total_students else 0
        )

        data = ReportSerializer({
            "total_students": total_students,
            "completed_tests": completed_tests,
            "pending_tests": max(total_students - completed_tests, 0),
            "completion_rate": round(completion_rate, 2),
            "average_score": round(avg_score, 2),
        }).data

        return Response(data)


# ----------------------------------------------------
# SUBSCRIPTION DEADLINE
# ----------------------------------------------------
class SubscriptionDeadlineAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrSchoolAdmin]

    def get(self, request):

        school = request.user.school

        if not school:
            return Response({"detail": "School not linked"}, status=400)

        expiry = school.created_at + timezone.timedelta(days=30)

        return Response({
            "subscription_expires_on": expiry
        })


# ----------------------------------------------------
# REFERRAL API
# ----------------------------------------------------
class ReferralAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrSchoolAdmin]

    def post(self, request):

        school = request.user.school

        serializer = SchoolReferralSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        SchoolReferral.objects.create(
            school=school,
            **serializer.validated_data
        )

        return Response(
            {"message": "Referral submitted successfully"},
            status=201
        )


# ----------------------------------------------------
# CONTACT API
# ----------------------------------------------------
class ContactAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):

        school = request.user.school

        serializer = ContactMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ContactMessage.objects.create(
            school=school,
            **serializer.validated_data
        )

        return Response(
            {"message": "Message sent successfully"},
            status=201
        )


# ----------------------------------------------------
# CLASS STUDENTS LIST
# ----------------------------------------------------
class ClassStudentListView(APIView):

    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrSchoolAdmin]

    def get(self, request):

        grade_id = request.query_params.get("grade_id")
        section_id = request.query_params.get("section_id")

        if not grade_id or not section_id:
            return Response(
                {"error": "grade_id and section_id required"},
                status=400
            )

        students = (
            StudentProfile.objects
            .filter(
                grade_id=grade_id,
                section_id=section_id,
                user__school=request.user.school,
                user__role=User.Role.STUDENT
            )
            .select_related("user", "grade", "section")
        )

        serializer = StudentListSerializer(students, many=True)

        return Response({
            "count": students.count(),
            "students": serializer.data
        })


# ----------------------------------------------------
# SCHOOL PROFILE
# ----------------------------------------------------
class SchoolProfileAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrSchoolAdmin]

    def get(self, request):

        school = request.user.school

        serializer = SchoolProfileSerializer({
            "user": request.user,
            "school": school
        })

        return Response(serializer.data)

    def put(self, request):

        serializer = SchoolProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        school = user.school
        data = serializer.validated_data

        if "admin_name" in data:
            parts = data["admin_name"].split(" ", 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ""

        if "admin_email" in data:
            user.email = data["admin_email"]

        if "admin_phone" in data:
            user.phone = data["admin_phone"]

        user.save()

        for field in ["school_name", "address", "city", "state", "pincode"]:
            if field in data:
                setattr(school, field, data[field])

        school.save()

        return Response({"message": "School profile updated successfully"})


# ----------------------------------------------------
# SCHOOL ADMIN DASHBOARD
# ----------------------------------------------------
class SchoolAdminDashboardAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrSchoolAdmin]

    def get(self, request):

        school = request.user.school

        total_students = StudentProfile.objects.filter(
            grade__school=school
        ).count()

        total_teachers = StaffProfile.objects.filter(
            user__school=school
        ).count()

        total_tests = CaseStudy.objects.filter(
            school=school
        ).count()

        attempts = StudentCaseStudyAttempt.objects.filter(
            student__school=school
        )

        avg_score = attempts.aggregate(avg=models.Avg("score"))["avg"] or 0

        recent_attempts = (
            attempts
            .select_related("student", "case_study")
            .order_by("-completed_at")[:5]
        )

        recent_activity = [
            {
                "student": a.student.username,
                "test": a.case_study.title,
                "score": a.score,
                "completed_at": a.completed_at,
            }
            for a in recent_attempts
        ]

        return Response({
            "stats": {
                "students": total_students,
                "teachers": total_teachers,
                "tests": total_tests,
            },
            "performance": {
                "average_score": round(avg_score, 2)
            },
            "recent_activity": recent_activity
        })
        
class StudentSearchAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrSchoolAdmin]

    def get(self, request):

        q = request.query_params.get("q")

        if not q:
            return Response(
                {"detail": "Search query 'q' is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        students = (
            StudentProfile.objects.filter(
                user__school=request.user.school
            )
            .filter(
                models.Q(user__first_name__icontains=q)
                | models.Q(user__last_name__icontains=q)
                | models.Q(user__username__icontains=q)
                | models.Q(admission_no__icontains=q)
            )
            .select_related("user", "grade", "section")
        )

        serializer = StudentListSerializer(students, many=True)

        return Response({
            "count": students.count(),
            "students": serializer.data
        })
        
class StudentsYearAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrSchoolAdmin]

    def get(self, request):

        grade_id = request.query_params.get("grade")
        section_id = request.query_params.get("section")

        students = StudentProfile.objects.filter(
            user__school=request.user.school
        )

        if grade_id:
            students = students.filter(grade_id=grade_id)

        if section_id:
            students = students.filter(section_id=section_id)

        students = students.select_related("user", "grade", "section")

        serializer = StudentListSerializer(students, many=True)

        return Response({
            "count": students.count(),
            "students": serializer.data
        })
        
class GlobalSearchAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        q = request.query_params.get("q")

        if not q:
            return Response(
                {"detail": "Search query 'q' required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        school = request.user.school

        students = (
            StudentProfile.objects.filter(
                user__school=school,
                user__first_name__icontains=q
            )
            .select_related("user")[:5]
        )

        tests = CaseStudy.objects.filter(
            school=school,
            title__icontains=q
        )[:5]

        chapters = TheoryTopic.objects.filter(
            school=school,
            title__icontains=q
        )[:5]

        return Response({
            "students": StudentListSerializer(students, many=True).data,
            "tests": TestSerializer(tests, many=True).data,
            "chapters": ChapterSerializer(chapters, many=True).data,
        })  