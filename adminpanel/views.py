import uuid

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg
from rest_framework import status
from accounts.permissions import IsSuperAdmin
from accounts.models import User, StudentProfile, StaffProfile
from core.models import School, SchoolRegistration
from learning.models import CaseStudy, StudentCaseStudyAttempt, TheoryTopic, CaseStudyAccess
from rest_framework.generics import ListAPIView
from django.db.models import Q
from django.db.models import OuterRef, Subquery, Value, BooleanField
from django.db.models.functions import Coalesce

from .serializers import AdminCaseStudySerializer, AdminTheoryTopicSerializer, AdminUserListSerializer, SchoolListSerializer, SchoolRegistrationListSerializer, AdminServiceSerializer,AdminQuestionSerializer,AdminAnswerOptionSerializer
from django.shortcuts import get_object_or_404
from accounts.models import User, StudentProfile, StaffProfile
from django.utils import timezone
from django.contrib.auth import get_user_model
from accounts.utils import generate_password
from accounts.email_utils import send_student_credentials
from learning.models import Service
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from learning.models import Question
from learning.models import Question, AnswerOption
import csv
from io import TextIOWrapper
from core.models import Grade
import unicodedata

from core.models import Grade
from rest_framework.generics import ListAPIView
from rest_framework import serializers

def generate_school_code():
    return f"SCH-{uuid.uuid4().hex[:6].upper()}"

def normalize(value):
    if value is None:
        return ""
    return unicodedata.normalize("NFKC", str(value)).strip()

def list_names(qs):
    return list(qs.values_list("name", flat=True))

User = get_user_model()

class SuperAdminDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        total_schools = School.objects.count()
        active_schools = School.objects.filter(is_active=True).count()

        total_students = StudentProfile.objects.count()
        total_staff = StaffProfile.objects.count()

        total_school_admins = User.objects.filter(
            role=User.Role.SCHOOL_ADMIN
        ).count()

        total_case_studies = CaseStudy.objects.count()
        total_attempts = StudentCaseStudyAttempt.objects.count()

        average_score = (
            StudentCaseStudyAttempt.objects.aggregate(avg=Avg("score"))["avg"]
            or 0
        )

        pending_registrations = SchoolRegistration.objects.filter(
            status="PENDING"
        ).count()

        total_services = Service.objects.count()
        active_services = Service.objects.filter(is_active=True).count()

        return Response({
            "schools": {
                "total": total_schools,
                "active": active_schools,
            },
            "users": {
                "students": total_students,
                "staff": total_staff,
                "school_admins": total_school_admins,
            },
            "learning": {
                "services": {
                    "total": total_services,
                    "active": active_services
                },
                "case_studies": total_case_studies,
                "attempts": total_attempts,
                "average_score": round(average_score, 2),
            },
            "registrations": {
                "pending": pending_registrations,
            }
        })

class SchoolListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = SchoolListSerializer

    def get_queryset(self):
        qs = School.objects.all().order_by("-created_at")

        search = self.request.query_params.get("search")
        is_active = self.request.query_params.get("is_active")

        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search)
            )

        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")

        return qs
    
class SchoolDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request, school_id):
        school = get_object_or_404(School, id=school_id)

        data = {
            "school": {
                "id": school.id,
                "name": school.name,
                "code": school.code,
                "email": school.email,
                "phone": school.phone,
                "is_active": school.is_active,
                "created_at": school.created_at,
            },
            "counts": {
                "students": StudentProfile.objects.filter(
                    grade__school=school
                ).count(),
                "staff": StaffProfile.objects.filter(
                    user__school=school
                ).count(),
                "school_admins": User.objects.filter(
                    role=User.Role.SCHOOL_ADMIN,
                    school=school
                ).count(),
                "case_studies": CaseStudy.objects.filter(
                    school=school
                ).count(),
                "attempts": StudentCaseStudyAttempt.objects.filter(
                    student__school=school
                ).count(),
            }
        }

        return Response(data)

class SchoolStatusUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def patch(self, request, school_id):
        school = get_object_or_404(School, id=school_id)

        raw_value = request.data.get("is_active")

        if raw_value is None:
            return Response(
                {"error": "is_active field is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Normalize value
        if isinstance(raw_value, bool):
            is_active = raw_value
        elif isinstance(raw_value, str):
            is_active = raw_value.lower() in ["true", "1", "yes"]
        else:
            is_active = bool(raw_value)

        school.is_active = is_active
        school.save(update_fields=["is_active"])

        return Response(
            {
                "message": "School status updated successfully",
                "school_id": school.id,
                "is_active": school.is_active,
            },
            status=status.HTTP_200_OK,
        )

class SchoolAnalyticsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request, school_id):
        school = get_object_or_404(School, id=school_id)

        attempts = StudentCaseStudyAttempt.objects.filter(
            student__school=school
        )

        total_students = StudentProfile.objects.filter(
            grade__school=school
        ).count()

        completed_students = attempts.values(
            "student_id"
        ).distinct().count()

        completion_rate = (
            (completed_students / total_students * 100)
            if total_students > 0 else 0
        )

        avg_score = attempts.aggregate(
            avg=Avg("score")
        )["avg"] or 0

        return Response({
            "school_id": school.id,
            "total_students": total_students,
            "completed_students": completed_students,
            "completion_rate": round(completion_rate, 2),
            "average_score": round(avg_score, 2),
        })
        

    
class ApproveSchoolRegistrationAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request, registration_id):
        registration = get_object_or_404(
            SchoolRegistration, id=registration_id
        )

        if registration.status != "PENDING":
            return Response(
                {"error": "This registration is already processed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create School
        school = School.objects.create(
            name=registration.school_name,
            code=generate_school_code(),
            email=registration.school_email,
            phone=registration.school_contact,
            address=registration.school_address,
            is_active=True,
        )

        # Create School Admin
        temp_password = generate_password()

        admin_user = User.objects.create_user(
            username=registration.school_email,
            email=registration.school_email,
            first_name=registration.school_principal_name,
            role=User.Role.SCHOOL_ADMIN,
            school=school,
            is_first_login=True,
            password=temp_password,
        )

        # Update registration
        registration.status = "APPROVED"
        registration.processed_at = timezone.now()
        registration.save()

        # Send email
        send_student_credentials(
            email=admin_user.email,
            username=admin_user.username,
            password=temp_password,
        )

        return Response(
            {
                "message": "School approved successfully",
                "school_id": school.id,
                "school_code": school.code,
                "admin_username": admin_user.username,
            },
            status=status.HTTP_201_CREATED,
        )
        
class RejectSchoolRegistrationAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request, registration_id):
        registration = get_object_or_404(
            SchoolRegistration, id=registration_id
        )

        if registration.status != "PENDING":
            return Response(
                {"error": "This registration is already processed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        registration.status = "REJECTED"
        registration.processed_at = timezone.now()
        registration.save()

        return Response(
            {"message": "School registration rejected"},
            status=status.HTTP_200_OK,
        )
        
class AdminUserListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = AdminUserListSerializer

    def get_queryset(self):
        qs = User.objects.select_related("school").all().order_by("-date_joined")

        role = self.request.query_params.get("role")
        school_id = self.request.query_params.get("school_id")
        is_active = self.request.query_params.get("is_active")
        search = self.request.query_params.get("search")

        if role:
            qs = qs.filter(role=role)

        if school_id:
            qs = qs.filter(school_id=school_id)

        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")

        if search:
            qs = qs.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        return qs
    
class AdminUserDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request, user_id):
        user = get_object_or_404(
            User.objects.select_related("school"),
            id=user_id,
        )

        serializer = AdminUserListSerializer(user)
        return Response(serializer.data)

class AdminUserStatusAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def patch(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        raw_value = request.data.get("is_active")
        if raw_value is None:
            return Response(
                {"error": "is_active field is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if isinstance(raw_value, bool):
            is_active = raw_value
        elif isinstance(raw_value, str):
            is_active = raw_value.lower() in ["true", "1", "yes"]
        else:
            is_active = bool(raw_value)

        user.is_active = is_active
        user.save(update_fields=["is_active"])

        return Response(
            {
                "message": "User status updated successfully",
                "user_id": user.id,
                "is_active": user.is_active,
            }
        )
class AdminUserResetPasswordAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        temp_password = generate_password()
        user.set_password(temp_password)
        user.is_first_login = True
        user.save(update_fields=["password", "is_first_login"])

        if user.email:
            send_student_credentials(
                email=user.email,
                username=user.username,
                password=temp_password,
            )

        return Response(
            {
                "message": "Password reset successfully",
                "user_id": user.id,
            },
            status=status.HTTP_200_OK,
        )
class AdminServiceListCreateAPIView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    queryset = Service.objects.all().order_by("-created_at")
    serializer_class = AdminServiceSerializer


class AdminServiceDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    queryset = Service.objects.all()
    serializer_class = AdminServiceSerializer
    
class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ["id", "name"]


class AdminGradeListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = GradeSerializer
    queryset = Grade.objects.all().order_by("name")
    
class AdminTheoryTopicListCreateAPIView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    queryset = TheoryTopic.objects.select_related("service", "parent")
    serializer_class = AdminTheoryTopicSerializer


class AdminTheoryTopicDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    queryset = TheoryTopic.objects.all()
    serializer_class = AdminTheoryTopicSerializer

class AdminCaseStudyListCreateAPIView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = AdminCaseStudySerializer

    def get_queryset(self):
        school_id = self.request.query_params.get("school_id")

        qs = CaseStudy.objects.select_related("service", "grade")

        if school_id:
            qs = qs.filter(school_id=school_id)

        # 🔥 LOCK STATUS FIX
        access_subquery = CaseStudyAccess.objects.filter(
            school_id=school_id,
            case_study_id=OuterRef("pk")
        ).values("is_locked")[:1]

        qs = qs.annotate(
            is_locked=Coalesce(
                Subquery(access_subquery),
                Value(False),
                output_field=BooleanField()
            )
        )

        return qs

class AdminCaseStudyDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    queryset = CaseStudy.objects.all()
    serializer_class = AdminCaseStudySerializer


class AdminQuestionListCreateAPIView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    queryset = Question.objects.select_related("case_study")
    serializer_class = AdminQuestionSerializer


class AdminQuestionDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    queryset = Question.objects.all()
    serializer_class = AdminQuestionSerializer


class AdminAnswerOptionListCreateAPIView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    queryset = AnswerOption.objects.select_related("question")
    serializer_class = AdminAnswerOptionSerializer


class AdminAnswerOptionDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    queryset = AnswerOption.objects.all()
    serializer_class = AdminAnswerOptionSerializer
    
class BulkQuestionUploadAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "CSV file is required"}, status=400)

        reader = csv.DictReader(TextIOWrapper(file.file, encoding="utf-8-sig"))

        created, errors = [], []

        for index, row in enumerate(reader, start=2):
            try:
                case_study = CaseStudy.objects.get(
                    title__iexact=normalize(row["Case Study Title"])
                )

                Question.objects.create(
                    case_study=case_study,
                    text=normalize(row["Question Text"]),
                    order=int(row.get("Order", 1))
                )

                created.append(index)

            except Exception as e:
                errors.append({"row": index, "error": str(e)})

        return Response({
            "created_count": len(created),
            "errors": errors
        })


class BulkOptionUploadAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "CSV file is required"}, status=400)

        reader = csv.DictReader(TextIOWrapper(file.file, encoding="utf-8-sig"))
        created, errors = [], []

        for index, row in enumerate(reader, start=2):
            try:
                case = CaseStudy.objects.get(
                    title__iexact=normalize(row["Case Study Title"])
                )

                question = Question.objects.get(
                    text__iexact=normalize(row["Question Text"]),
                    case_study=case
                )

                is_correct = normalize(row["Is Correct (yes/no)"]).lower() in ["yes", "true"]

                if is_correct:
                    AnswerOption.objects.filter(
                        question=question, is_correct=True
                    ).update(is_correct=False)

                AnswerOption.objects.create(
                    question=question,
                    text=normalize(row["Option Text"]),
                    is_correct=is_correct
                )

                created.append(index)

            except Exception as e:
                errors.append({"row": index, "error": str(e)})

        return Response({
            "created_count": len(created),
            "errors": errors
        })

class BulkTheoryTopicUploadAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "CSV file is required"}, status=400)

        reader = csv.DictReader(TextIOWrapper(file.file, encoding="utf-8-sig"))
        created, errors = [], []

        for index, row in enumerate(reader, start=2):
            try:
                school = School.objects.get(
                    name__iexact=normalize(row["School Name"])
                )

                service = Service.objects.get(
                    name__iexact=normalize(row["Service Name"]),
                    school=school
                )

                grade = Grade.objects.get(
                    name__iexact=normalize(row["Grade Name"]),
                    school=school
                )

                parent = None
                parent_title = normalize(row.get("Parent Topic"))
                if parent_title:
                    parent = TheoryTopic.objects.get(
                        title__iexact=parent_title,
                        service=service,
                        grade=grade
                    )

                topic = TheoryTopic.objects.create(
                    school=school,
                    service=service,
                    grade=grade,
                    title=normalize(row["Topic Title"]),
                    description=normalize(row["Description"]),
                    parent=parent,
                    order=int(row.get("Order", 1))
                )

                created.append({"row": index, "id": topic.id})

            except Exception as e:
                errors.append({"row": index, "error": str(e)})

        return Response({
            "created_count": len(created),
            "created": created,
            "errors": errors
        })

class BulkCaseStudyUploadAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "CSV file is required"}, status=400)

        reader = csv.DictReader(
            TextIOWrapper(file.file, encoding="utf-8-sig")
        )

        created, errors = [], []

        for index, row in enumerate(reader, start=2):
            try:
                # 🔒 FIX HEADER ISSUES
                row = {k.strip(): v for k, v in row.items()}

                school_name = normalize(row.get("School Name"))
                service_name = normalize(row.get("Service Name"))
                grade_name = normalize(row.get("Grade Name"))

                if not school_name:
                    raise ValueError("School Name column is missing or empty in CSV")

                school = School.objects.filter(
                    name__iexact=school_name
                ).first()
                if not school:
                    raise ValueError(
                        f'School "{school_name}" not found. '
                        f'Available: {list_names(School.objects.all())}'
                    )

                service = Service.objects.filter(
                    name__iexact=service_name,
                    school=school
                ).first()
                if not service:
                    raise ValueError(f'Service "{service_name}" not found')

                grade = Grade.objects.filter(
                    name__iexact=grade_name,
                    school=school
                ).first()
                if not grade:
                    raise ValueError(f'Grade "{grade_name}" not found')

                case = CaseStudy.objects.create(
                    school=school,
                    service=service,
                    grade=grade,
                    title=normalize(row.get("Topic Title")),
                    description=normalize(row.get("Description")),
                    created_by=request.user,
                )

                created.append({"row": index, "id": case.id})

            except Exception as e:
                errors.append({"row": index, "error": str(e)})

        return Response({
            "created_count": len(created),
            "created": created,
            "errors": errors
        })
class SchoolRegistrationListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = SchoolRegistrationListSerializer
    queryset = SchoolRegistration.objects.all().order_by("-created_at")

    def get_queryset(self):
        qs = super().get_queryset()

        status_filter = self.request.query_params.get("status")
        search = self.request.query_params.get("search")

        if status_filter:
            qs = qs.filter(status=status_filter)

        if search:
            qs = qs.filter(
                Q(school_name__icontains=search) |
                Q(school_email__icontains=search)
            )

        return qs
    
class ToggleCaseStudyLockAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        school_id = request.data.get("school_id")
        case_study_id = request.data.get("case_study_id")
        is_locked = request.data.get("is_locked", True)

        if not school_id or not case_study_id:
            return Response({"error": "Missing data"}, status=400)

        access, _ = CaseStudyAccess.objects.get_or_create(
            school_id=school_id,
            case_study_id=case_study_id
        )

        access.is_locked = is_locked
        access.save()

        return Response({
            "message": "Lock updated",
            "case_study_id": case_study_id,
            "is_locked": access.is_locked
        })