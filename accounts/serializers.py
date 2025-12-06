# accounts/serializers.py
from rest_framework import serializers
from accounts.models import User, StudentProfile
from core.models import Grade, Section, School


class StudentCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)

    grade_id = serializers.IntegerField()
    section_id = serializers.IntegerField()
    admission_no = serializers.CharField(max_length=50)

    # Only needed if SUPERADMIN is creating students for another school
    school_id = serializers.IntegerField(required=False)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already in use")
        return value

    def validate(self, attrs):
        grade_id = attrs.get("grade_id")
        section_id = attrs.get("section_id")
        school_id = attrs.get("school_id")

        request = self.context.get("request")
        creator = request.user

        # Determine which school to use
        if creator.role == User.Role.SUPERADMIN:
            if not school_id:
                raise serializers.ValidationError("school_id is required for superadmin")
            try:
                school = School.objects.get(id=school_id)
            except School.DoesNotExist:
                raise serializers.ValidationError("Invalid school_id")
        else:
            # School admin / staff must belong to a school
            if not creator.school:
                raise serializers.ValidationError("Your account is not linked to any school")
            school = creator.school

        # Validate grade & section belong to this school
        try:
            grade = Grade.objects.get(id=grade_id, school=school)
        except Grade.DoesNotExist:
            raise serializers.ValidationError("Invalid grade_id for this school")

        try:
            section = Section.objects.get(id=section_id, school=school, grade=grade)
        except Section.DoesNotExist:
            raise serializers.ValidationError("Invalid section_id for this grade/school")

        attrs["school"] = school
        attrs["grade"] = grade
        attrs["section"] = section
        return attrs

    def create(self, validated_data):
        school = validated_data.pop("school")
        grade = validated_data.pop("grade")
        section = validated_data.pop("section")

        password = validated_data.pop("password")

        user = User.objects.create_user(
            username=validated_data.get("username"),
            password=password,
            email=validated_data.get("email", ""),
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            role=User.Role.STUDENT,
            school=school,
            is_active=True,
        )

        student_profile = StudentProfile.objects.create(
            user=user,
            grade=grade,
            section=section,
            admission_no=validated_data.get("admission_no"),
        )

        return user
