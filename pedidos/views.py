from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Categoria, Plato, Pedido, ItemPedido, ItemPedido, Reseña
from .forms import ReseñaForm
from django.http import HttpResponse, Http404
from django.utils.encoding import smart_str
from django.conf import settings
from django.contrib.auth.decorators import login_required

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

    if not request.user.is_authenticated:
        return redirect('login')

    cart = _get_cart(request)
    cart[str(plato_id)] = cart.get(str(plato_id), 0) + 1
    request.session.modified = True
    
    return redirect(request.META.get('HTTP_REFERER', 'pedidos:menu'))

def remove_from_cart(request, plato_id):
    """
    Elimina un ítem (plato) del carrito por completo.
    """
    cart = _get_cart(request)
    cart.pop(str(plato_id), None)
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
        plato = get_object_or_404(Plato, pk=int(pid))
        subtotal = plato.precio * cant
        items.append({'plato': plato, 'cantidad': cant, 'subtotal': subtotal})
        total += subtotal
    return render(request, 'pedidos/cart.html', {'items': items, 'total': total})


def home(request):
    """
    Muestra la página de inicio (Home).
    """
    return render(request, 'pedidos/home.html')

def menu(request):
    """
    Muestra la página del Menú, filtrada por categorías.
    Lee el parámetro '?tab=' de la URL para decidir qué mostrar.
    """
    current_tab = request.GET.get('tab', 'Especiales')
    
    if current_tab == 'Especiales':
        menu_data = Categoria.objects.prefetch_related('platos').all()
    else:
        menu_data = Categoria.objects.prefetch_related('platos').filter(nombre=current_tab)
    
    return render(request, 'pedidos/menu.html', {'categorias': menu_data})

def contacto(request):
    """
    Muestra la página estática de 'Contacto' con la
    información del restaurante.
    """
    return render(request, 'pedidos/contacto.html')

def reseñas(request):
    """
    Muestra la lista de reseñas y permite a usuarios
    autenticados enviar una nueva.
    """
    form = ReseñaForm()
    
    if request.method == 'POST':
        # Solo procesamos el formulario si el usuario está logueado
        if not request.user.is_authenticated:
            return redirect('login') 
            
        form = ReseñaForm(request.POST)
        if form.is_valid():
            # Guardamos la reseña pero sin enviarla a la BD todavía
            reseña = form.save(commit=False) 
            # Asignamos el usuario actual
            reseña.usuario = request.user 
            reseña.save() # Ahora sí la guardamos
            
            messages.success(request, '¡Gracias por tu reseña!')
            return redirect('pedidos:reseñas')

    # Para todos (GET y POST fallido), mostramos la lista de reseñas
    lista_reseñas = Reseña.objects.all().order_by('-creado')
    
    context = {
        'reseñas': lista_reseñas,
        'form': form
    }
    return render(request, 'pedidos/reseñas.html', context)


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

        user = request.user if request.user.is_authenticated else None
        
        pedido = Pedido.objects.create(
            usuario=user,
            nombre=nombre,
            telefono=telefono,
            direccion=direccion,
            estado='PREP',      
            repartidor=None     
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

@login_required
def order_detail(request, pedido_id):
    """
    Muestra la página de "Orden Completada" con los detalles.
    Ahora valida que el pedido le pertenezca al usuario logueado.
    """
    pedido = get_object_or_404(Pedido, pk=pedido_id, usuario=request.user)
    
    # Si el pedido_id existe pero no pertenece al request.user,
    # get_object_or_404 lanzará un error 404 (No Encontrado),
    # protegiendo los datos de otros usuarios.

    return render(request, 'pedidos/order_detail.html', {'pedido': pedido})

def plato_imagen(request, pk):
    """
    Sirve las imágenes de los platos desde bytes en BD.
    Si no hay imagen, redirige a un placeholder estático.
    """
    plato = get_object_or_404(Plato, pk=pk)

    # Si no hay bytes, redirige al placeholder (cumple con el test)
    if not getattr(plato, "imagen_bytes", None):
        # Ajusta la ruta al placeholder según tu estructura de static
        # Ejemplos: "img/placeholder.png" o "pedidos/img/placeholder.png"
        return redirect(f"{settings.STATIC_URL}img/placeholder.png")

    content_type = plato.imagen_mime or "image/jpeg"
    resp = HttpResponse(plato.imagen_bytes, content_type=content_type)

    # Opcional: nombre de archivo sugerido (descarga/buscadores)
    resp["Content-Disposition"] = f'inline; filename="{smart_str(f"plato_{pk}.jpg")}"'
    resp["Cache-Control"] = "public, max-age=86400"
    return resp