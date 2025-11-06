import pytest
from pedidos.models import Categoria, Plato, Pedido, ItemPedido

def test_mo_002_item_subtotal(item):
    assert item.subtotal() == item.cantidad * item.precio_unitario

def test_mo_001_pedido_suma_total(pedido, item, db):
    # crea otro item para el mismo pedido
    from model_bakery import baker
    other = baker.make("pedidos.ItemPedido", pedido=pedido, precio_unitario=1000, cantidad=3)
    assert pedido.total() == item.subtotal() + other.subtotal()

