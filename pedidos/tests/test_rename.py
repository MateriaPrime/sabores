# pedidos/tests/test_rename.py

import pytest
from django.urls import reverse

# (No hay parches de 'humanize' aquí)

@pytest.mark.django_db
def test_add_to_cart_agrega_uno(client, plato):
    # Esta prueba ya pasa (¡Éxito!)
    r = client.post(reverse('pedidos:add_to_cart', args=[plato.id]), follow=True)
    assert r.status_code == 200
    # Revisa el contenido de la página 'menu.html'
    assert b"Especiales" in r.content 

    cart = client.session.get('cart', {})
    assert str(plato.id) in cart
    assert cart[str(plato.id)] == 1

@pytest.mark.django_db
def test_add_mismo_plato_incrementa(client, plato):
    # Esta prueba ya pasa (¡Éxito!)
    client.post(reverse('pedidos:add_to_cart', args=[plato.id]))
    client.post(reverse('pedidos:add_to_cart', args=[plato.id]))
    cart = client.session.get('cart', {})
    assert cart[str(plato.id)] == 2

@pytest.mark.django_db
def test_remove_from_cart_elimina(client, plato):
    # Esta prueba ya pasa (¡Éxito!)
    client.post(reverse('pedidos:add_to_cart', args=[plato.id]))
    client.post(reverse('pedidos:remove_from_cart', args=[plato.id]))
    cart = client.session.get('cart', {})
    assert str(plato.id) not in cart

@pytest.mark.django_db
def test_cart_vacio_mensaje(client):
    # Esta prueba ahora pasará gracias al fixture en conftest.py
    r = client.get(reverse('pedidos:cart'))
    assert r.status_code == 200
    # Revisa el texto de 'cart.html'
    assert b"tu carrito esta vacio" in r.content.lower()