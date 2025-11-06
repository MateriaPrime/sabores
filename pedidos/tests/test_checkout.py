import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_checkout_crea_pedido(carrito_lleno):
    from pedidos.models import Pedido

    before = Pedido.objects.count()
    payload = {
        # Campos típicos que muchas vistas de checkout piden:
        "nombre": "Xisco Tester",
        "direccion": "Calle Falsa 123",
        "telefono": "999999999",
        "metodo_pago": "efectivo",   # si tu form usa otro valor, cámbialo
        "confirmar": "1",            # si no usas 'confirmar', no pasa nada
    }
    resp = carrito_lleno.post(reverse("pedidos:checkout"), data=payload, follow=True)

    # Debe responder 200/302 (OK o redirect a detalle/éxito)
    assert resp.status_code in (200, 302)
    after = Pedido.objects.count()
    assert after == before + 1, "No se creó el Pedido; revisa los nombres de campos que requiere tu formulario de checkout."


@pytest.mark.django_db
def test_checkout_valida_obligatorios(carrito_lleno):
    from pedidos.models import Pedido

    before = Pedido.objects.count()
    resp = carrito_lleno.post(reverse("pedidos:checkout"), data={}, follow=True)
    after = Pedido.objects.count()

    # 1) No debe crear pedido
    assert after == before, "Se creó un Pedido aun sin datos obligatorios."

    # 2) Debe quedarse en la página de checkout o devolver 400 (según tu implementación)
    assert resp.status_code in (200, 400)