from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import SignupClienteForm
from .models import Pedido 
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .forms import SignupClienteForm, PlatoAdminForm, SignupRepartidorForm # Importamos PlatoAdminForm
from .models import Pedido, Plato # Importamos Plato

def signup_cliente(request):
    if request.method == 'POST':
        form = SignupClienteForm(request.POST)
        if form.is_valid():
            user = form.save()
            cliente_group, _ = Group.objects.get_or_create(name='CLIENTE')
            user.groups.add(cliente_group)
            login(request, user)
            return redirect('dashboard_router')
    else:
        form = SignupClienteForm()
    return render(request, 'pedidos/signup_cliente.html', {'form': form})

@login_required
def dash_cliente(request):
    # Cliente ve SOLO sus pedidos (si guardas nombre/teléfono en Pedido, lo ideal es relacionarlo al usuario)
    mis_pedidos = Pedido.objects.filter(usuario=request.user).order_by('-creado')
    # Si prefieres, añade un FK: Pedido.usuario = ForeignKey(User, null=True) y filtra por usuario
    return render(request, 'pedidos/dash_cliente.html', {'pedidos': mis_pedidos})

def is_repartidor(u):
    return u.is_authenticated and u.groups.filter(name='REPARTIDOR').exists()

@login_required
@user_passes_test(is_repartidor)
def dash_repartidor(request):
    # Lógica para el panel del repartidor
    
    # 1. Pedidos disponibles (en preparación y sin repartidor asignado)
    pedidos_disponibles = Pedido.objects.filter(
        estado='PREP', 
        repartidor__isnull=True
    ).prefetch_related('items__plato').order_by('creado')

    # 2. Mis pedidos (los que acepté y están 'En camino')
    mis_pedidos = Pedido.objects.filter(
        repartidor=request.user, 
        estado='CAM'
    ).prefetch_related('items__plato').order_by('creado')
    
    context = {
        'pedidos_disponibles': pedidos_disponibles,
        'mis_pedidos_aceptados': mis_pedidos
    }
    return render(request, 'pedidos/dash_repartidor.html', context)

@login_required
@user_passes_test(is_repartidor)
def pedido_aceptar(request, pedido_id):
    """
    Esta vista se activa cuando un repartidor presiona "Aceptar".
    """
    pedido = get_object_or_404(Pedido, id=pedido_id, estado='PREP', repartidor__isnull=True)
    
    # Asignamos el pedido al repartidor actual y cambiamos el estado
    pedido.repartidor = request.user
    pedido.estado = 'CAM' # 'CAM' = En Camino
    pedido.save()
    
    messages.success(request, f"Pedido #{pedido.id} aceptado. ¡En camino!")
    return redirect('pedidos:dash_repartidor')

@login_required
@user_passes_test(is_repartidor)
def pedido_entregado(request, pedido_id):
    """
    Esta vista se activa cuando un repartidor presiona "Marcar como Entregado".
    """
    # Buscamos un pedido que me pertenezca a MÍ y esté 'En Camino'
    pedido = get_object_or_404(Pedido, id=pedido_id, repartidor=request.user, estado='CAM')
    
    pedido.estado = 'ENT' # 'ENT' = Entregado
    pedido.save()
    
    messages.success(request, f"Pedido #{pedido.id} marcado como entregado.")
    return redirect('pedidos:dash_repartidor')

def is_admin(u):
    """ Helper para chequear si el usuario es superuser """
    return u.is_authenticated and u.is_superuser

@login_required
@user_passes_test(is_admin) # Solo superusuarios
def plato_crear(request):
    """ Vista para CREAR un nuevo plato """
    if request.method == 'POST':
        # Pasamos request.FILES para manejar la subida de la imagen
        form = PlatoAdminForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Plato creado exitosamente.")
            return redirect('pedidos:menu')
    else:
        form = PlatoAdminForm()
    
    return render(request, 'pedidos/plato_form.html', {
        'form': form,
        'titulo': 'Añadir Nuevo Plato'
    })

@login_required
@user_passes_test(is_admin) # Solo superusuarios
def plato_editar(request, pk):
    """ Vista para EDITAR un plato existente """
    plato = get_object_or_404(Plato, pk=pk) # Obtenemos el plato
    if request.method == 'POST':
        form = PlatoAdminForm(request.POST, request.FILES, instance=plato)
        if form.is_valid():
            form.save()
            messages.success(request, f"Plato '{plato.nombre}' actualizado.")
            return redirect('pedidos:menu')
    else:
        # Creamos el form precargado con los datos del plato
        form = PlatoAdminForm(instance=plato) 
    
    return render(request, 'pedidos/plato_form.html', {
        'form': form,
        'titulo': f'Editar: {plato.nombre}'
    })

@login_required
@user_passes_test(is_admin) # Solo superusuarios
def plato_eliminar(request, pk):
    """ Vista para ELIMINAR un plato """
    plato = get_object_or_404(Plato, pk=pk)
    if request.method == 'POST':
        # Si el usuario confirma (vía POST), eliminamos
        nombre_plato = plato.nombre
        plato.delete()
        messages.success(request, f"Plato '{nombre_plato}' eliminado.")
        return redirect('pedidos:menu')
    
    # Si es GET, mostramos la página de confirmación
    return render(request, 'pedidos/plato_confirm_delete.html', {'plato': plato})

# VISTA DE REGISTRO PARA REPARTIDORES
def signup_repartidor(request):
    if request.method == 'POST':
        form = SignupRepartidorForm(request.POST) # Usa el nuevo formulario
        if form.is_valid():
            user = form.save()
            # Asigna al grupo 'REPARTIDOR'
            repartidor_group, _ = Group.objects.get_or_create(name='REPARTIDOR')
            user.groups.add(repartidor_group)
            
            login(request, user) # Inicia sesión
            return redirect('dashboard_router') # Lo manda al router
    else:
        form = SignupRepartidorForm() # Muestra el formulario vacío
    
    return render(request, 'pedidos/signup_repartidor.html', {'form': form})