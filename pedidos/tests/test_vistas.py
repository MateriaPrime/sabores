import pytest
from django.urls import reverse
from pedidos.models import Categoria, Plato

@pytest.mark.django_db
def test_home_200(client):
    r = client.get(reverse('pedidos:home'))
    assert r.status_code == 200

@pytest.mark.django_db
def test_menu_lista_categorias_y_platos(client):
    cat = Categoria.objects.create(nombre="Sopas")
    Plato.objects.create(categoria=cat, nombre="Cazuela", precio=5990)
    r = client.get(reverse('pedidos:menu'))
    assert r.status_code == 200
    assert b"Sopas" in r.content
    assert b"Cazuela" in r.content

@pytest.mark.django_db
def test_menu_sin_platos_muestra_estado_vacio(client):
    r = client.get(reverse('pedidos:menu'))
    assert r.status_code == 200
    # pon aquí el texto que muestras cuando no hay platos
    # assert b"No hay platos" in r.content
