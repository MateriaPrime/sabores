import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_add_to_cart_agrega_uno(client, plato):
    r = client.post(reverse('pedidos:add_to_cart', args=[plato.id]), follow=True)
    assert r.status_code == 200
    # comprueba que algo del template del carrito aparece
    assert b"Carrito" in r.content
    # opcional: inspeccionar sesión
    cart = client.session.get('cart', {})
    assert str(plato.id) in cart
    assert cart[str(plato.id)]['cantidad'] == 1

@pytest.mark.django_db
def test_add_mismo_plato_incrementa(client, plato):
    client.post(reverse('pedidos:add_to_cart', args=[plato.id]))
    client.post(reverse('pedidos:add_to_cart', args=[plato.id]))
    cart = client.session.get('cart', {})
    assert cart[str(plato.id)]['cantidad'] == 2

@pytest.mark.django_db
def test_remove_from_cart_elimina(client, plato):
    client.post(reverse('pedidos:add_to_cart', args=[plato.id]))
    client.post(reverse('pedidos:remove_from_cart', args=[plato.id]))
    cart = client.session.get('cart', {})
    assert str(plato.id) not in cart

@pytest.mark.django_db
def test_cart_vacio_mensaje(client):
    r = client.get(reverse('pedidos:cart'))
    assert r.status_code == 200
    assert b"carrito" in r.content.lower()  # busca tu mensaje de vacio
