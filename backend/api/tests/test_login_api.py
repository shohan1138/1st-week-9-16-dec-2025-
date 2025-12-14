import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from api.models import EMAILOTP
from django.utils import timezone
from datetime import timedelta

client = APIClient()


@pytest.mark.django_db
def test_login_success():
    user = User.objects.create_user(
        username="loginuser",
        email="login@test.com",
        password="StrongPass123"
    )

    EMAILOTP.objects.create(
        user=user,
        otp_code="123456",
        is_used=True,
        expires_at=timezone.now() + timedelta(minutes=2)
    )

    payload = {
        "email": "login@test.com",
        "password": "StrongPass123"
    }

    response = client.post(reverse("login"), payload, format="json")

    assert response.status_code == 200
    assert response.data["detail"] == "Login successful."
    assert "token" in response.data


@pytest.mark.django_db
def test_login_wrong_password():
    user = User.objects.create_user(
        username="wrongpass",
        email="wrong@test.com",
        password="StrongPass123"
    )

    EMAILOTP.objects.create(
        user=user,
        otp_code="111111",
        is_used=True,
        expires_at=timezone.now() + timedelta(minutes=2)
    )

    payload = {
        "email": "wrong@test.com",
        "password": "WrongPassword"
    }

    response = client.post(reverse("login"), payload, format="json")

    assert response.status_code == 401
    assert response.data["detail"] == "Invalid credentials."


@pytest.mark.django_db
def test_login_unverified_user():
    user = User.objects.create_user(
        username="unverified",
        email="unverified@test.com",
        password="StrongPass123"
    )

    payload = {
        "email": "unverified@test.com",
        "password": "StrongPass123"
    }

    response = client.post(reverse("login"), payload, format="json")

    assert response.status_code == 403
    assert response.data["detail"] == "Account not verified."
