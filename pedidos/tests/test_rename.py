# pedidos/tests/test_rename.py
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def user(db):
    return User.objects.create_user(username="test", password="secret")

@pytest.fixture
def client_logeado(client, user):
    client.login(username="test", password="secret")
    return client

@pytest.mark.django_db
def test_add_to_cart_agrega_uno(client_logeado, plato):
    # Seteamos un REFERER para que la vista redirija ahí
    referer = reverse("pedidos:menu")
    r = client_logeado.post(
        reverse("pedidos:add_to_cart", args=[plato.id]),
        follow=True,
        HTTP_REFERER=referer,
    )
    assert r.status_code == 200

    # Verifica que el carrito en sesión tenga el plato con cantidad 1
    cart = client_logeado.session.get("cart", {})
    assert cart.get(str(plato.id)) == 1

    # Opcional: estamos en el menú (por el referer)
    html = r.content.decode().lower()
    assert "menú" in html or "menu" in html or "sabores" in html

@pytest.mark.django_db
def test_add_mismo_plato_incrementa(client_logeado, plato):
    client_logeado.post(reverse("pedidos:add_to_cart", args=[plato.id]), HTTP_REFERER=reverse("pedidos:menu"))
    client_logeado.post(reverse("pedidos:add_to_cart", args=[plato.id]), HTTP_REFERER=reverse("pedidos:menu"))

    cart = client_logeado.session.get("cart", {})
    assert cart.get(str(plato.id)) == 2, f"Estructura de cart inesperada: {cart}"

@pytest.mark.django_db
def test_cart_vacio_mensaje(client):
    r = client.get(reverse("pedidos:cart"))
    assert r.status_code == 200
    html = r.content.decode().lower()
    # Mensaje exacto de tu template vacío
    assert "tu carrito está vacío" in html or "tu carrito esta vacio" in html
