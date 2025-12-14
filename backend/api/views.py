from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import EMAILOTP
from django.conf import settings
import random
from rest_framework import generics
from .serializers import UserSerializer, VerifyOTPSerializer, LoginSerializer
from rest_framework.permissions import  AllowAny
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from api.models import EMAILOTP
from rest_framework.permissions import AllowAny






class createUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        otp = str(random.randint(100000, 999999))
        EMAILOTP.objects.create(
            user=user,
            otp_code=otp,
        )
        send_mail(
        subject="Your OTP Verification Code",
        message=f"Your OTP is {otp}. It will expire in 2 minutes.",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=False,
        )

        print("OTP:", otp)
class VerifyOTPView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp']

            try:
                user = User.objects.get(email=email)
                otp_entry = EMAILOTP.objects.get(user=user, otp_code=otp_code, is_used=False)

                if otp_entry.expires_at < timezone.now():
                    return Response({"detail": "OTP has expired."}, status=status.HTTP_400_BAD_REQUEST)

                otp_entry.is_used = True
                otp_entry.save()

                return Response({"detail": "OTP verified successfully."}, status=status.HTTP_200_OK)

            except User.DoesNotExist:
                return Response({"detail": "User with this email does not exist."}, status=status.HTTP_400_BAD_REQUEST)
            except EMAILOTP.DoesNotExist:
                return Response({"detail": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not EMAILOTP.objects.filter(user=user, is_used=True).exists():
            return Response(
                {"detail": "Account not verified."},
                status=status.HTTP_403_FORBIDDEN
            )

        user = authenticate(username=user.username, password=password)
        if not user:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "detail": "Login successful.",
                "token": token.key
            },
            status=status.HTTP_200_OK
        )