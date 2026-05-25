import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.clients.models import ClientCompany


@pytest.mark.django_db
def test_client_company_create_name_only():
    c = ClientCompany.objects.create(name="Acme Ltd")
    assert c.name == "Acme Ltd"
    assert c.address == ""
    assert c.phone == ""


@pytest.mark.django_db
def test_client_company_create_all_fields():
    c = ClientCompany.objects.create(
        name="Beta Co",
        address="1 High St\nTown",
        phone="+1 555 0100",
    )
    assert c.name == "Beta Co"
    assert "High St" in c.address
    assert c.phone == "+1 555 0100"


@pytest.mark.django_db
def test_client_company_full_clean_rejects_blank_name():
    c = ClientCompany(name="   ")
    with pytest.raises(ValidationError):
        c.full_clean()


@pytest.mark.django_db
def test_client_company_full_clean_strips_name():
    c = ClientCompany(name="  Trimmed  ", address="", phone="")
    c.full_clean()
    c.save()
    c.refresh_from_db()
    assert c.name == "Trimmed"


@pytest.mark.django_db
def test_client_company_ordering_by_name():
    ClientCompany.objects.create(name="Zebra Inc")
    ClientCompany.objects.create(name="Alpha LLC")
    names = list(ClientCompany.objects.values_list("name", flat=True))
    assert names == ["Alpha LLC", "Zebra Inc"]


@pytest.mark.django_db
def test_multiple_client_companies_allowed():
    ClientCompany.objects.create(name="One")
    ClientCompany.objects.create(name="Two")
    assert ClientCompany.objects.count() == 2


@pytest.mark.django_db
def test_client_list_requires_login(client):
    response = client.get(reverse("client_list"))
    assert response.status_code == 302
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_client_create_flow_name_only(client):
    user = User.objects.create_user(username="op", email="op@example.com", password="pass12345")
    client.force_login(user)
    response = client.post(
        reverse("client_create"),
        {"name": "Solo Client", "address": "", "phone": ""},
    )
    assert response.status_code == 302
    assert response.url == reverse("client_list")
    c = ClientCompany.objects.get()
    assert c.name == "Solo Client"
    assert c.address == ""
    assert c.phone == ""


@pytest.mark.django_db
def test_client_create_flow_all_fields(client):
    user = User.objects.create_user(username="op2", email="op2@example.com", password="pass12345")
    client.force_login(user)
    response = client.post(
        reverse("client_create"),
        {
            "name": "Full Co",
            "address": "99 Oak Ave",
            "phone": "+44 20 7946 0958",
        },
    )
    assert response.status_code == 302
    c = ClientCompany.objects.get(name="Full Co")
    assert c.address == "99 Oak Ave"
    assert c.phone == "+44 20 7946 0958"


@pytest.mark.django_db
def test_client_edit_clears_optional_fields(client):
    user = User.objects.create_user(username="op3", email="op3@example.com", password="pass12345")
    client.force_login(user)
    c = ClientCompany.objects.create(
        name="Edit Me",
        address="Old addr",
        phone="000",
    )
    response = client.post(
        reverse("client_edit", kwargs={"pk": c.pk}),
        {"name": "Edit Me", "address": "", "phone": ""},
    )
    assert response.status_code == 302
    c.refresh_from_db()
    assert c.address == ""
    assert c.phone == ""


@pytest.mark.django_db
def test_client_list_shows_records(client):
    user = User.objects.create_user(username="op4", email="op4@example.com", password="pass12345")
    client.force_login(user)
    ClientCompany.objects.create(name="Listed Co")
    response = client.get(reverse("client_list"))
    assert response.status_code == 200
    assert b"Listed Co" in response.content


@pytest.mark.django_db
def test_client_delete_requires_login(client):
    c = ClientCompany.objects.create(name="Gone Co")
    r = client.post(reverse("client_delete", kwargs={"pk": c.pk}))
    assert r.status_code == 302
    assert ClientCompany.objects.filter(pk=c.pk).exists()


@pytest.mark.django_db
def test_client_delete_post_removes_and_redirects(client):
    user = User.objects.create_user(username="del1", email="d1@example.com", password="pass12345")
    client.force_login(user)
    c = ClientCompany.objects.create(name="Delete Me")
    r = client.post(reverse("client_delete", kwargs={"pk": c.pk}))
    assert r.status_code == 302
    assert r.url == reverse("client_list")
    assert not ClientCompany.objects.filter(pk=c.pk).exists()


@pytest.mark.django_db
def test_client_delete_get_not_allowed(client):
    user = User.objects.create_user(username="del2", email="d2@example.com", password="pass12345")
    client.force_login(user)
    c = ClientCompany.objects.create(name="Stay Co")
    r = client.get(reverse("client_delete", kwargs={"pk": c.pk}))
    assert r.status_code == 405
    assert ClientCompany.objects.filter(pk=c.pk).exists()


@pytest.mark.django_db
def test_client_create_rejects_missing_name(client):
    user = User.objects.create_user(username="op5", email="op5@example.com", password="pass12345")
    client.force_login(user)
    response = client.post(
        reverse("client_create"),
        {"name": "", "address": "x", "phone": "y"},
    )
    assert response.status_code == 200
    assert ClientCompany.objects.count() == 0
