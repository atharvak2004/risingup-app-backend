from django.contrib import admin
from .models import School, Grade, Section, SchoolRegistration

admin.site.register(School)
admin.site.register(Grade)
admin.site.register(Section)
admin.site.register(SchoolRegistration)
