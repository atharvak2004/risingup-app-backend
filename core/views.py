from rest_framework import generics, permissions
from .models import SchoolRegistration
from .serializers import SchoolRegistrationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import check_password
from rest_framework import status
from .models import SchoolRegistration, Grade
from .serializers import SchoolRegistrationSerializer, GradeSerializer

class SchoolRegistrationCreateView(generics.CreateAPIView):
    
    queryset = SchoolRegistration.objects.all()
    serializer_class = SchoolRegistrationSerializer
    permission_classes = [permissions.AllowAny]

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        user = request.user

        if not old_password or not new_password:
            return Response(
                {"error": "Both old and new passwords are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check old password
        if not user.check_password(old_password):
            return Response(
                {"error": "Old password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update password
        user.set_password(new_password)
        user.is_first_login = False
        user.save()

        return Response(
            {"message": "Password updated successfully"},
            status=status.HTTP_200_OK
        )

class GradeListView(generics.ListAPIView):
    serializer_class = GradeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        school_id = self.request.query_params.get("school_id")

        if not school_id:
            return Grade.objects.none()

        return Grade.objects.filter(school_id=school_id).order_by("order")
