import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_plato_imagen_con_bytes(client, plato):
    # simula imagen cargada en BD
    plato.imagen_bytes = b'\x89PNG\r\n\x1a\n'  # cabecera PNG mínima
    plato.imagen_mime = 'image/png'
    plato.imagen_nombre = 'test.png'
    plato.save()

    r = client.get(reverse('pedidos:plato_imagen', args=[plato.id]))
    assert r.status_code == 200
    assert r['Content-Type'].startswith('image/')

@pytest.mark.django_db
def test_plato_imagen_sin_bytes_redirige_placeholder(client, plato):
    r = client.get(reverse('pedidos:plato_imagen', args=[plato.id]))
    # con tu fallback debería redirigir (302) a estático
    assert r.status_code in (301, 302)
