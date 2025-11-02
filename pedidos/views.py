from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Categoria, Plato, Pedido, ItemPedido
from django.http import HttpResponse, Http404

class MockPlatoManager:
    """Simula el manager .platos.all() de Django."""
    def __init__(self, platos_list):
        self.platos_list = platos_list
    def all(self):
        return self.platos_list

class MockCategoria:
    """Simula un objeto Categoria para un filtro específico."""
    def __init__(self, nombre, platos_list):
        self.nombre = nombre
        self.platos = MockPlatoManager(platos_list)
        
    def __str__(self): return self.nombre
    
    @property
    def pk(self): return 0


def _get_cart(request):
    """
    Carrito en sesión: {'plato_id': cantidad}
    """
    return request.session.setdefault('cart', {})

def home(request):
    return render(request, 'pedidos/home.html')

def menu(request):
    current_tab = request.GET.get('tab', 'Especiales')
    
    dish_filters = {
        'Sopas': ['Cazuela de vacuno', 'Sopa de mariscos'],
        'Platos principales': ['Tallarines con salsa', 'Porotos con rienda'],
        'Postres': ['Mousse de chocolate', 'Pie de limón'],
    }

    if current_tab == 'Especiales':
        menu_data = Categoria.objects.prefetch_related('platos').all()
    else:
        required_dish_names = dish_filters.get(current_tab, [])
        
        filtered_platos = Plato.objects.filter(nombre__in=required_dish_names)

        menu_data = [MockCategoria(nombre=current_tab, platos_list=list(filtered_platos))]
    
    return render(request, 'pedidos/menu.html', {'categorias': menu_data})

def add_to_cart(request, plato_id):
    cart = _get_cart(request)
    cart[str(plato_id)] = cart.get(str(plato_id), 0) + 1
    request.session.modified = True
    messages.success(request, 'Agregado al carrito.')
    return redirect('pedidos:menu')

def remove_from_cart(request, plato_id):
    cart = _get_cart(request)
    cart.pop(str(plato_id), None)
    request.session.modified = True
    return redirect('pedidos:cart')

def cart(request):
    cart = _get_cart(request)
    items = []
    total = 0
    for pid, cant in cart.items():
        plato = get_object_or_404(Plato, pk=int(pid))
        subtotal = plato.precio * cant
        items.append({'plato': plato, 'cantidad': cant, 'subtotal': subtotal})
        total += subtotal
    return render(request, 'pedidos/cart.html', {'items': items, 'total': total})

def checkout(request):
    """
    Form demo: nombre, teléfono, dirección.
    Crea Pedido + Items y limpia carrito.
    """
    cart = _get_cart(request)
    if request.method == 'POST' and cart:
        nombre = request.POST.get('nombre', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        direccion = request.POST.get('direccion', '').strip()

        if not (nombre and telefono and direccion):
            messages.error(request, 'Completa todos los datos.')
            return redirect('pedidos:cart')

        pedido = Pedido.objects.create(
            nombre=nombre, telefono=telefono, direccion=direccion
        )
        for pid, cant in cart.items():
            plato = get_object_or_404(Plato, pk=int(pid))
            ItemPedido.objects.create(
                pedido=pedido, plato=plato, cantidad=cant, precio_unitario=plato.precio
            )

        request.session['cart'] = {}
        request.session.modified = True
        return redirect('pedidos:order_detail', pedido_id=pedido.id)

    return redirect('pedidos:cart')

def order_detail(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    return render(request, 'pedidos/order_detail.html', {'pedido': pedido})


def plato_imagen(request, pk):
    plato = get_object_or_404(Plato, pk=pk)
    if not plato.imagen_bytes:
        raise Http404("Este plato no tiene imagen guardada")
    resp = HttpResponse(plato.imagen_bytes, content_type=plato.imagen_mime or 'image/jpeg')
    if plato.imagen_nombre:
        resp['Content-Disposition'] = f'inline; filename="{plato.imagen_nombre}"'
    resp['Cache-Control'] = 'public, max-age=86400'
    return resp