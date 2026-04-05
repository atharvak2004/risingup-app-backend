import django_filters
from accounts.models import StudentProfile


class StudentFilter(django_filters.FilterSet):

    grade = django_filters.NumberFilter(field_name="grade_id")
    section = django_filters.NumberFilter(field_name="section_id")
    admission_no = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = StudentProfile
        fields = ["grade", "section", "admission_no"]