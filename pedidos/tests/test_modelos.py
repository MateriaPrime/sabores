import pytest
from pedidos.models import Categoria, Plato, Pedido, ItemPedido

@pytest.mark.django_db
def test_total_de_pedido():
    cat = Categoria.objects.create(nombre="Platos")
    p1 = Plato.objects.create(categoria=cat, nombre="A", precio=3000)
    p2 = Plato.objects.create(categoria=cat, nombre="B", precio=2000)
    ped = Pedido.objects.create(nombre="X", telefono="123", direccion="Calle 1")

    # Act
    ItemPedido.objects.create(pedido=ped, plato=p1, cantidad=2, precio_unitario=p1.precio)
    ItemPedido.objects.create(pedido=ped, plato=p2, cantidad=1, precio_unitario=p2.precio)

    # Assert
    assert ped.total() == 8000
