from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from .models import Categoria, Plato, Pedido, ItemPedido, Reseña
from .forms import ReseñaForm

# --- LÓGICA DEL CARRITO ---

def _get_cart(request):
    return request.session.setdefault('cart', {})

def add_to_cart(request, plato_id):
    cart = _get_cart(request)
    cart[str(plato_id)] = cart.get(str(plato_id), 0) + 1
    request.session.modified = True
    messages.success(request, 'Agregado.')
    return redirect(request.META.get('HTTP_REFERER', 'pedidos:menu'))

def remove_from_cart(request, plato_id):
    cart = _get_cart(request)
    if str(plato_id) in cart:
        del cart[str(plato_id)]
        request.session.modified = True
    return redirect('pedidos:cart')

def cart(request):
    cart = _get_cart(request)
    items = []
    total = 0
    for pid, cant in cart.items():
        plato = get_object_or_404(Plato, pk=int(pid))
        subtotal = plato.precio * cant
        total += subtotal
        items.append({'plato': plato, 'cantidad': cant, 'subtotal': subtotal})
    return render(request, 'pedidos/cart.html', {'items': items, 'total': total})

# --- VISTAS PÚBLICAS ---

def home(request):
    return render(request, 'pedidos/home.html')

def menu(request):
    tab = request.GET.get('tab', 'Especiales')
    if tab == 'Especiales':
        cats = Categoria.objects.prefetch_related('platos').all()
    else:
        cats = Categoria.objects.prefetch_related('platos').filter(nombre=tab)
    return render(request, 'pedidos/menu.html', {'categorias': cats})

def contacto(request):
    return render(request, 'pedidos/contacto.html')

def reseñas(request):
    # Simplificamos la lógica del formulario en pocas líneas
    form = ReseñaForm(request.POST or None)
    
    if request.method == 'POST' and request.user.is_authenticated and form.is_valid():
        reseña = form.save(commit=False)
        reseña.usuario = request.user
        reseña.save()
        messages.success(request, '¡Gracias por tu reseña!')
        return redirect('pedidos:reseñas')
    
    lista = Reseña.objects.all().order_by('-creado')
    return render(request, 'pedidos/reseñas.html', {'reseñas': lista, 'form': form})

# --- PAGO Y PEDIDOS ---

def checkout(request):
    cart = _get_cart(request)
    if request.method != 'POST' or not cart:
        return redirect('pedidos:cart')

    if not request.user.is_authenticated:
        messages.error(request, 'Inicia sesión para pagar.')
        return redirect('login')

    # Recolectar datos
    nombre = request.POST.get('nombre', '').strip()
    telefono = request.POST.get('telefono', '').strip()
    direccion = request.POST.get('direccion', '').strip()

    if not all([nombre, telefono, direccion]):
        messages.error(request, 'Faltan datos de entrega.')
        return redirect('pedidos:cart')

    # 1. Calcular total y preparar objetos (Optimizamos para no consultar la BD dos veces)
    total_pedido = 0
    platos_procesados = [] # Lista temporal: [(ObjetoPlato, cantidad), ...]
    
    for pid, cant in cart.items():
        plato = get_object_or_404(Plato, pk=int(pid))
        total_pedido += plato.precio * cant
        platos_procesados.append((plato, cant))

    # 2. Verificar Saldo y Cobrar
    perfil = request.user.perfil
    if perfil.saldo < total_pedido:
        messages.error(request, f"Saldo insuficiente. Tienes ${perfil.saldo} y necesitas ${total_pedido}.")
        return redirect('pedidos:cart')

    perfil.saldo -= total_pedido
    perfil.save()

    # 3. Crear Pedido
    pedido = Pedido.objects.create(
        usuario=request.user,
        nombre=nombre, telefono=telefono, direccion=direccion,
        estado='PREP', repartidor=None
    )

    # 4. Crear Items (Usando la lista que ya preparamos)
    for plato, cant in platos_procesados:
        ItemPedido.objects.create(
            pedido=pedido, plato=plato, cantidad=cant, precio_unitario=plato.precio
        )

    # 5. Limpiar y Redirigir
    request.session['cart'] = {}
    request.session.modified = True
    messages.success(request, f"¡Pago exitoso! Nuevo saldo: ${perfil.saldo}")
    
    return redirect('pedidos:order_detail', pedido_id=pedido.id)

@login_required
def order_detail(request, pedido_id):
    # Verifica que el pedido pertenezca al usuario para seguridad
    pedido = get_object_or_404(Pedido, pk=pedido_id, usuario=request.user)
    return render(request, 'pedidos/order_detail.html', {'pedido': pedido})

def plato_imagen(request, pk):
    plato = get_object_or_404(Plato, pk=pk)
    if not plato.imagen_bytes: raise Http404
    return HttpResponse(plato.imagen_bytes, content_type=plato.imagen_mime or 'image/jpeg')