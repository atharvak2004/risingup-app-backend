# accounts/serializers.py
from rest_framework import serializers
from accounts.models import User, StudentProfile
from core.models import Grade, Section, School
from accounts.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
import csv
from io import TextIOWrapper
from accounts.utils import generate_unique_username, generate_password
from accounts.email_utils import send_student_credentials
class StudentCreateSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField()
    birth_date = serializers.DateField()

    grade_id = serializers.IntegerField()
    section_id = serializers.IntegerField()
    admission_no = serializers.CharField(max_length=50)
    school_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        request = self.context["request"]
        creator = request.user

        # School resolution
        if creator.role == User.Role.SUPERADMIN:
            school = School.objects.get(id=attrs["school_id"])
        else:
            school = creator.school

        grade = Grade.objects.get(id=attrs["grade_id"], school=school)
        section = Section.objects.get(id=attrs["section_id"], grade=grade)

        attrs["school"] = school
        attrs["grade"] = grade
        attrs["section"] = section
        return attrs

    def create(self, validated_data):
        # Extract relations
        school = validated_data.pop("school")
        grade = validated_data.pop("grade")
        section = validated_data.pop("section")

        birth_year = validated_data["birth_date"].year
        first_name = validated_data["first_name"]

        # 1️⃣ Generate username + password
        username = generate_unique_username(first_name, birth_year)
        temp_password = generate_password()

        # 2️⃣ Create user
        user = User.objects.create_user(
            username=username,
            password=temp_password,  # hashed internally
            first_name=first_name,
            last_name=validated_data.get("last_name", ""),
            email=validated_data["email"],
            role=User.Role.STUDENT,
            school=school,
            is_first_login=True,
            is_active=True,
        )

        # 3️⃣ Student profile
        StudentProfile.objects.create(
            user=user,
            grade=grade,
            section=section,
            admission_no=validated_data["admission_no"],
        )

        # 4️⃣ Email credentials
        send_student_credentials(
            email=user.email,
            username=username,
            password=temp_password,
        )

        return user


class StudentBulkCreateSerializer(serializers.Serializer):
    students = StudentCreateSerializer(many=True)

    def create(self, validated_data):
        request = self.context["request"]

        created = []
        errors = []

        for student_data in validated_data["students"]:
            serializer = StudentCreateSerializer(
                data=student_data,
                context={"request": request},
            )

            try:
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
                created.append({"id": user.id, "username": user.username})
            except serializers.ValidationError as e:
                errors.append({
                    "username": student_data.get("username"),
                    "error": e.detail,
                })

        return {"created": created, "errors": errors}


class StudentCSVUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def create(self, validated_data):
        request = self.context["request"]
        file = validated_data["file"]

        decoded_file = TextIOWrapper(file.file, encoding="utf-8")
        reader = csv.DictReader(decoded_file)

        required_fields = {
            "first_name",
            "last_name",
            "email",
            "birth_date",
            "grade_id",
            "section_id",
            "admission_no",
        }

        if not required_fields.issubset(reader.fieldnames):
            raise serializers.ValidationError(
                f"CSV must contain fields: {', '.join(required_fields)}"
            )

        created = []
        errors = []

        for index, row in enumerate(reader, start=2):
            serializer = StudentCreateSerializer(
                data={
                    "first_name": row.get("first_name"),
                    "last_name": row.get("last_name", ""),
                    "email": row.get("email"),
                    "birth_date": row.get("birth_date"),
                    "grade_id": row.get("grade_id"),
                    "section_id": row.get("section_id"),
                    "admission_no": row.get("admission_no"),
                },
                context={"request": request},
            )

            try:
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
                created.append({
                    "row": index,
                    "id": user.id,
                    "username": user.username,
                })
            except serializers.ValidationError as e:
                errors.append({
                    "row": index,
                    "email": row.get("email"),
                    "error": e.detail,
                })

        return {
            "created_count": len(created),
            "created": created,
            "errors": errors,
        }



class SchoolLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid username or password")

        if not user.is_active:
            raise serializers.ValidationError("User is inactive")

        # Only allow SCHOOL_ADMIN or STAFF or STUDENT or SUPERADMIN
        # If you want only SCHOOL_ADMIN to login, uncomment this:
        # if user.role not in [User.Role.SCHOOL_ADMIN]:
        #     raise serializers.ValidationError("Not allowed to login")

        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "school_id": user.school.id if user.school else None,
                "school_name": user.school.name if user.school else None,
                "is_first_login": user.is_first_login,
            }
        }
        
class StudentLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid username or password")

        if not user.is_active:
            raise serializers.ValidationError("User is inactive")

        if user.role != User.Role.STUDENT:
            raise serializers.ValidationError("Only students can login here")

        attrs["user"] = user
        return attrs
    
class StudentProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone"]

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.email = validated_data.get("email", instance.email)
        instance.phone = validated_data.get("phone", instance.phone)

        instance.save()
        return instance