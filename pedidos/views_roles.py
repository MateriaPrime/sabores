from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib.auth import login, logout
from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import SignupClienteForm
from .models import Pedido 
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .forms import SignupClienteForm, PlatoAdminForm, SignupRepartidorForm, PerfilUpdateForm
from .models import Pedido, Plato, Perfil

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
    mis_pedidos = Pedido.objects.filter(usuario=request.user).order_by('-creado')
    return render(request, 'pedidos/dash_cliente.html', {'pedidos': mis_pedidos})

def is_repartidor(u):
    return u.is_authenticated and u.groups.filter(name='REPARTIDOR').exists()

@login_required
@user_passes_test(is_repartidor)
def dash_repartidor(request):
    
    pedidos_disponibles = Pedido.objects.filter(
        estado='PREP', 
        repartidor__isnull=True
    ).prefetch_related('items__plato').order_by('creado')

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
    
    pedido.repartidor = request.user
    pedido.estado = 'CAM'
    pedido.save()
    
    messages.success(request, f"Pedido #{pedido.id} aceptado. ¡En camino!")
    return redirect('pedidos:dash_repartidor')

@login_required
@user_passes_test(is_repartidor)
def pedido_entregado(request, pedido_id):
    """
    Esta vista se activa cuando un repartidor presiona "Marcar como Entregado".
    """
    pedido = get_object_or_404(Pedido, id=pedido_id, repartidor=request.user, estado='CAM')
    
    pedido.estado = 'ENT'
    
    messages.success(request, f"Pedido #{pedido.id} marcado como entregado.")
    return redirect('pedidos:dash_repartidor')

def is_admin(u):
    """ Helper para chequear si el usuario es superuser """
    return u.is_authenticated and u.is_superuser

@login_required
@user_passes_test(is_admin)
def plato_crear(request):
    """ Vista para CREAR un nuevo plato """
    if request.method == 'POST':
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
@user_passes_test(is_admin)
def plato_editar(request, pk):
    """ Vista para EDITAR un plato existente """
    plato = get_object_or_404(Plato, pk=pk)
    if request.method == 'POST':
        form = PlatoAdminForm(request.POST, request.FILES, instance=plato)
        if form.is_valid():
            form.save()
            messages.success(request, f"Plato '{plato.nombre}' actualizado.")
            return redirect('pedidos:menu')
    else:
        form = PlatoAdminForm(instance=plato) 
    
    return render(request, 'pedidos/plato_form.html', {
        'form': form,
        'titulo': f'Editar: {plato.nombre}'
    })

@login_required
@user_passes_test(is_admin) 
def plato_eliminar(request, pk):
    """ Vista para ELIMINAR un plato """
    plato = get_object_or_404(Plato, pk=pk)
    if request.method == 'POST':
        nombre_plato = plato.nombre
        plato.delete()
        messages.success(request, f"Plato '{nombre_plato}' eliminado.")
        return redirect('pedidos:menu')
    
    return render(request, 'pedidos/plato_confirm_delete.html', {'plato': plato})

def signup_repartidor(request):
    if request.method == 'POST':
        form = SignupRepartidorForm(request.POST)
        if form.is_valid():
            user = form.save()
            repartidor_group, _ = Group.objects.get_or_create(name='REPARTIDOR')
            user.groups.add(repartidor_group)
            
            login(request, user)
            return redirect('dashboard_router') 
    else:
        form = SignupRepartidorForm() 
    
    return render(request, 'pedidos/signup_repartidor.html', {'form': form})

@login_required
def perfil_editar(request):
    """ Vista para que el cliente edite su nombre, apellido, dirección y teléfono. """
    user_instance = request.user
    
    if request.method == 'POST':
        form = PerfilUpdateForm(request.POST, instance=user_instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Tu perfil ha sido actualizado con éxito.")
            return redirect('pedidos:dash_cliente')
        else:
            messages.error(request, "Hubo un error al actualizar tu perfil. Revisa los campos.")
    else:
        form = PerfilUpdateForm(instance=user_instance)
    
    return render(request, 'pedidos/perfil_form.html', {
        'form': form,
        'titulo': 'Editar mi perfil',
    })


@login_required
def perfil_eliminar_confirmar(request):
    """ 
    Vista para: 1. Mostrar la confirmación (GET). 
                2. Eliminar la cuenta (POST) y redirigir al login.
    """
    if request.method == 'POST':
        user = request.user
        
        user.delete()
        
        logout(request)
        
        messages.success(request, "Tu cuenta ha sido eliminada con éxito. ¡Vuelve pronto!")
        return redirect('pedidos:home')
    
    return render(request, 'pedidos/perfil_confirm_delete.html')