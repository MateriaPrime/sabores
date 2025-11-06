# pedidos/tests/conftest.py
import pytest
from model_bakery import baker
from decimal import Decimal
from django.urls import reverse

@pytest.fixture
def user(db, django_user_model):
    return django_user_model.objects.create_user(username="test", password="secret")

@pytest.fixture
def plato(db):
    # NO pongas precio aquí si Plato no tiene ese campo
    return baker.make("pedidos.Plato", nombre="Churrasco")

@pytest.fixture
def client_logeado(client, user):
    client.login(username="test", password="secret")
    return client

@pytest.fixture
def carrito_lleno(client_logeado, plato, db):
    """
    Pobla el carrito pasando SIEMPRE por la vista real 'add_to_cart'.
    Probamos múltiples nombres de parámetro para cantidad (cantidad/quantity)
    por si tu formulario usa otro nombre.
    """
    url = reverse("pedidos:add_to_cart", args=[plato.id])

    # Intento 1: 'cantidad'
    resp = client_logeado.post(url, data={"cantidad": 2}, follow=True)

    # Si tu vista exige otro nombre, intentamos 'quantity'
    if resp.status_code not in (200, 302) or "cart" not in client_logeado.session:
        resp = client_logeado.post(url, data={"quantity": 2}, follow=True)

    # Verificación mínima: hay algo en la sesión del carrito
    assert "cart" in client_logeado.session or "carrito" in client_logeado.session, \
        "La vista add_to_cart no pobló la sesión; revisa el nombre de la key (cart/carrito) y el parámetro de cantidad."

    return client_logeado
