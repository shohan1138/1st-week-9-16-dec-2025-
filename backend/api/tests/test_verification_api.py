import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from api.models import EMAILOTP

client = APIClient()


@pytest.mark.django_db
def test_verify_otp_success():
    """
    OTP is correct, not expired, not used
    """
    user = User.objects.create_user(
        username="otpuser",
        email="otpuser@test.com",
        password="StrongPass123"
    )

    otp = EMAILOTP.objects.create(
        user=user,
        otp_code="123456",
        expires_at=timezone.now() + timedelta(minutes=2)
    )

    payload = {
        "email": user.email,
        "otp": "123456"
    }

    response = client.post(reverse("verify-otp"), payload, format="json")

    assert response.status_code == 200
    assert response.data["detail"] == "OTP verified successfully."

    otp.refresh_from_db()
    assert otp.is_used is True


@pytest.mark.django_db
def test_verify_otp_invalid():
    """
    OTP is wrong
    """
    user = User.objects.create_user(
        username="wrongotp",
        email="wrongotp@test.com",
        password="StrongPass123"
    )

    EMAILOTP.objects.create(
        user=user,
        otp_code="111111",
        expires_at=timezone.now() + timedelta(minutes=2)
    )

    payload = {
        "email": user.email,
        "otp": "999999"
    }

    response = client.post(reverse("verify-otp"), payload, format="json")

    assert response.status_code == 400
    assert response.data["detail"] == "Invalid OTP."


@pytest.mark.django_db
def test_verify_otp_expired():
    """
    OTP expired (120 seconds over)
    """
    user = User.objects.create_user(
        username="expiredotp",
        email="expired@test.com",
        password="StrongPass123"
    )

    EMAILOTP.objects.create(
        user=user,
        otp_code="222222",
        expires_at=timezone.now() - timedelta(seconds=1)
    )

    payload = {
        "email": user.email,
        "otp": "222222"
    }

    response = client.post(reverse("verify-otp"), payload, format="json")

    assert response.status_code == 400
    assert response.data["detail"] == "OTP has expired."


@pytest.mark.django_db
def test_verify_otp_already_used():
    """
    OTP already verified once
    """
    user = User.objects.create_user(
        username="usedotp",
        email="used@test.com",
        password="StrongPass123"
    )

    EMAILOTP.objects.create(
        user=user,
        otp_code="333333",
        is_used=True,
        expires_at=timezone.now() + timedelta(minutes=2)
    )

    payload = {
        "email": user.email,
        "otp": "333333"
    }

    response = client.post(reverse("verify-otp"), payload, format="json")

    assert response.status_code == 400
    assert response.data["detail"] == "Invalid OTP."
