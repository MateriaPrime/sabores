import pytest
from django.urls import reverse
from pedidos.models import Pedido

@pytest.mark.django_db
def test_checkout_crea_pedido(carrito_lleno):
    client = carrito_lleno
    data = {"nombre":"Cliente","telefono":"999","direccion":"Calle 123"}
    r = client.post(reverse('pedidos:checkout'), data, follow=True)
    assert r.status_code == 200

    ped = Pedido.objects.latest('id')
    assert ped.items.count() == 1
    assert ped.total() > 0
    # carrito vacío tras compra
    assert client.session.get('cart', {}) == {}

@pytest.mark.django_db
def test_checkout_valida_obligatorios(carrito_lleno):
    client = carrito_lleno
    r = client.post(reverse('pedidos:checkout'), {"nombre":"", "telefono":"", "direccion":""})
    # Mantén 200 si re-renderizas con errores, o 400 si devuelves bad request
    assert r.status_code in (200, 400)
    # y no se crea pedido
    assert not Pedido.objects.exists()
