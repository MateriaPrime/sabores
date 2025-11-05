from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Categoria, Plato, Pedido, ItemPedido
from django.http import HttpResponse, Http404

# --- SECCIÓN DEL CARRITO DE COMPRAS ---

def _get_cart(request):
    """
    Función interna para obtener el carrito de la sesión.
    Se guarda como un diccionario: {'plato_id': cantidad}
    """
    return request.session.setdefault('cart', {})

def add_to_cart(request, plato_id):
    """
    Agrega un plato (o incrementa su cantidad) en el carrito de la sesión.
    """
    cart = _get_cart(request)
    cart[str(plato_id)] = cart.get(str(plato_id), 0) + 1
    request.session.modified = True  # Marcamos la sesión como modificada
    messages.success(request, 'Agregado al carrito.')
    
    # Redirige de vuelta a la página anterior (o al menú por defecto)
    return redirect(request.META.get('HTTP_REFERER', 'pedidos:menu'))

def remove_from_cart(request, plato_id):
    """
    Elimina un ítem (plato) del carrito por completo.
    """
    cart = _get_cart(request)
    cart.pop(str(plato_id), None)  # pop() elimina la llave del diccionario
    request.session.modified = True
    return redirect('pedidos:cart')

def cart(request):
    """
    Muestra la página del carrito, calculando subtotales y el total.
    """
    cart = _get_cart(request)
    items = []
    total = 0
    for pid, cant in cart.items():
        # Buscamos el plato en la BD
        plato = get_object_or_404(Plato, pk=int(pid))
        subtotal = plato.precio * cant
        items.append({'plato': plato, 'cantidad': cant, 'subtotal': subtotal})
        total += subtotal
    return render(request, 'pedidos/cart.html', {'items': items, 'total': total})

# --- SECCIÓN DE VISTAS DE PÁGINAS (Home, Menú) ---

def home(request):
    """
    Muestra la página de inicio (Home).
    """
    # Esta vista puede modificarse para enviar platos destacados al home.html
    return render(request, 'pedidos/home.html')

def menu(request):
    """
    Muestra la página del Menú, filtrada por categorías.
    Lee el parámetro '?tab=' de la URL para decidir qué mostrar.
    """
    # Obtiene la pestaña actual de la URL. Si no hay, usa 'Especiales'
    current_tab = request.GET.get('tab', 'Especiales')
    
    if current_tab == 'Especiales':
        # Si es 'Especiales', carga TODAS las categorías y sus platos
        menu_data = Categoria.objects.prefetch_related('platos').all()
    else:
        # Si es otra pestaña (ej. 'Platos principales'),
        # filtra la Categoría cuyo nombre coincida con la pestaña.
        menu_data = Categoria.objects.prefetch_related('platos').filter(nombre=current_tab)
    
    return render(request, 'pedidos/menu.html', {'categorias': menu_data})

# --- SECCIÓN DE PROCESAMIENTO DE PEDIDOS (Checkout) ---

def checkout(request):
    """
    Procesa el pago (Checkout).
    Toma los datos del carrito y del formulario POST para crear
    un Pedido y sus Items correspondientes.
    """
    cart = _get_cart(request)
    if request.method == 'POST' and cart:
        nombre = request.POST.get('nombre', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        direccion = request.POST.get('direccion', '').strip()

        if not (nombre and telefono and direccion):
            messages.error(request, 'Completa todos los datos.')
            return redirect('pedidos:cart')

        # Asigna el usuario si está logueado
        user = request.user if request.user.is_authenticated else None
        
        # --- [INICIO] ESTA ES LA CORRECCIÓN ---
        # Creamos el Pedido y asignamos los valores explícitamente
        # para asegurarnos de que coincida con la consulta del repartidor.
        pedido = Pedido.objects.create(
            usuario=user,
            nombre=nombre,
            telefono=telefono,
            direccion=direccion,
            estado='PREP',      # <-- Lo ponemos explícitamente
            repartidor=None     # <-- Lo ponemos explícitamente
        )
        # --- [FIN] CORRECCIÓN ---
        
        # Crea un ItemPedido por cada plato en el carrito
        for pid, cant in cart.items():
            plato = get_object_or_404(Plato, pk=int(pid))
            ItemPedido.objects.create(
                pedido=pedido, plato=plato, cantidad=cant, precio_unitario=plato.precio
            )

        # Limpia el carrito de la sesión
        request.session['cart'] = {}
        request.session.modified = True
        
        # Redirige al detalle de la orden recién creada
        return redirect('pedidos:order_detail', pedido_id=pedido.id)

    return redirect('pedidos:cart')

def order_detail(request, pedido_id):
    """
    Muestra la página de "Orden Completada" con los detalles.
    """
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    return render(request, 'pedidos/order_detail.html', {'pedido': pedido})

# --- SECCIÓN DE UTILIDADES (Imágenes) ---

def plato_imagen(request, pk):
    """
    Vista especial para servir las imágenes de los platos.
    Lee los bytes de la imagen desde la BD y los devuelve como respuesta.
    """
    plato = get_object_or_404(Plato, pk=pk)
    if not plato.imagen_bytes:
        raise Http404("Este plato no tiene imagen guardada")
    
    # Responde con los bytes de la imagen y el tipo de contenido (ej. 'image/jpeg')
    resp = HttpResponse(plato.imagen_bytes, content_type=plato.imagen_mime or 'image/jpeg')
    
    # Ayuda al navegador a cachear la imagen por 1 día (86400 segundos)
    resp['Cache-Control'] = 'public, max-age=86400'
    return resp