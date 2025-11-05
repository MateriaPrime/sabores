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
from .forms import SignupClienteForm, PlatoAdminForm # Importamos PlatoAdminForm
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
    # Aquí solo entran REPARTIDORES
    return render(request, 'pedidos/dash_repartidor.html')

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
# --- FIN DE LAS NUEVAS VISTAS ---