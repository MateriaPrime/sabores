import pytest
from django.urls import reverse
from pedidos.models import Categoria, Plato, Pedido, ItemPedido
from django.template.engine import Engine  # Importar Engine

@pytest.fixture
def categoria(db):
    return Categoria.objects.create(nombre="Principales")

@pytest.fixture
def plato(categoria):
    return Plato.objects.create(categoria=categoria, nombre="Tallarin", precio=5000)

@pytest.fixture
def carrito_lleno(client, plato):
    # simula POST a tu view de carrito (ajusta si tu URL difiere)
    client.post(reverse('pedidos:add_to_cart', args=[plato.id]))
    return client  # el client ahora tiene la sesión con carrito

@pytest.fixture
def pedido_con_items(db, plato):
    p = Pedido.objects.create(nombre="Cliente", telefono="123", direccion="Mi casa")
    ItemPedido.objects.create(pedido=p, plato=plato, cantidad=2, precio_unitario=plato.precio)
    return p

# --- INICIO CORRECCIÓN 'intcomma' (Versión para Django 4.0+) ---
@pytest.fixture(autouse=True)
def humanize_patch():
    try:
        # Esta es la forma moderna de añadir built-ins
        Engine.get_default().builtins.append('django.contrib.humanize.templatetags.humanize')
    except Exception:
        pass # Evita errores si ya está cargado
# --- FIN CORRECCIÓN ---