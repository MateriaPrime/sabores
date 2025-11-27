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
    """
    Panel del repartidor. Muestra pedidos disponibles y pedidos en curso.
    """
    # 1. Pedidos disponibles (en preparación y sin repartidor)
    # Excluye los que este usuario haya rechazado previamente
    pedidos_disponibles = Pedido.objects.filter(
        estado='PREP', 
        repartidor__isnull=True
    ).exclude(
        repartidores_que_rechazaron=request.user
    ).prefetch_related('items__plato').order_by('creado')

    # 2. Mis pedidos (los que acepté)
    # IMPORTANTE: Filtramos por estado='CAM'. 
    # Esto hace que los pedidos 'ENT' (Entregados) desaparezcan de la lista.
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
def cargar_saldo(request):
    """
    Simula una carga de dinero a la billetera del usuario.
    """
    if request.method == 'POST':
        try:
            monto = int(request.POST.get('monto', 0))
            if monto > 0:
                # Sumamos el monto al saldo del perfil
                perfil = request.user.perfil
                perfil.saldo += monto
                perfil.save()
                messages.success(request, f"¡Carga exitosa! Se han añadido ${monto} a tu billetera.")
            else:
                messages.error(request, "El monto debe ser mayor a 0.")
        except ValueError:
            messages.error(request, "Monto inválido.")
            
    return redirect('pedidos:dash_cliente')

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
def pedido_rechazar(request, pedido_id):
    """
    Esta vista se activa cuando un repartidor presiona "Rechazar".
    Añade al repartidor a la lista de "rechazados" de ese pedido.
    """
    # Buscamos el pedido
    pedido = get_object_or_404(Pedido, id=pedido_id, estado='PREP')
    
    # Añadimos al repartidor actual a la lista M2M de rechazados
    pedido.repartidores_que_rechazaron.add(request.user)
    
    messages.info(request, f"Pedido #{pedido.id} rechazado. No se mostrará de nuevo.")
    return redirect('pedidos:dash_repartidor')

@login_required
@user_passes_test(is_repartidor)
def pedido_entregado(request, pedido_id):
    """
    Marca el pedido como entregado.
    """
    pedido = get_object_or_404(Pedido, id=pedido_id, repartidor=request.user, estado='CAM')
    
    # Cambiamos el estado a 'ENT' (Entregado)
    pedido.estado = 'ENT' 
    pedido.save()
    
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