from django.urls import path
from .views import VerifyOTPView
from api.views import LoginView

urlpatterns = [
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("login/", LoginView.as_view(), name="login"),
]
