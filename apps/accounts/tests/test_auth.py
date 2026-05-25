import pytest
from django.contrib.auth.models import User
from django.urls import reverse


@pytest.mark.django_db
def test_login_success_redirects_to_dashboard(client):
    User.objects.create_user(username="operator", email="op@example.com", password="pass12345")

    response = client.post(reverse("login"), {"username": "operator", "password": "pass12345"})

    assert response.status_code == 302
    assert response.url == reverse("dashboard")


@pytest.mark.django_db
def test_login_invalid_credentials_shows_error(client):
    User.objects.create_user(username="operator", email="op@example.com", password="pass12345")

    response = client.post(reverse("login"), {"username": "operator", "password": "wrong-pass"})

    assert response.status_code == 200
    assert "Въведете коректно потребителско име и парола.".encode() in response.content


@pytest.mark.django_db
def test_dashboard_requires_authentication(client):
    response = client.get(reverse("dashboard"))

    assert response.status_code == 302
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_logout_ends_session(client):
    user = User.objects.create_user(
        username="operator", email="op@example.com", password="pass12345"
    )
    client.force_login(user)

    response = client.post(reverse("logout"))

    assert response.status_code == 302
    assert response.url == reverse("login")
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_password_reset_page_loads(client):
    response = client.get(reverse("password_reset"))

    assert response.status_code == 200
    assert "Нулиране на парола".encode() in response.content
