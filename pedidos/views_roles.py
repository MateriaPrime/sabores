from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import SignupClienteForm
from .models import Pedido  # asumiendo que tu modelo Pedido está en esta app

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
