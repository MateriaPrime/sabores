# pedidos/admin_views.py
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Perfil  # <--- IMPORTANTE: Importamos el modelo Perfil

def staff_required(view_func):
    return user_passes_test(lambda u: u.is_staff)(view_func)

# Helper para verificar si es superusuario (para temas de dinero)
def is_superuser_check(u):
    return u.is_authenticated and u.is_superuser

@staff_required
def gestionar_usuarios(request):
    usuarios = User.objects.all().order_by("username")
    roles = Group.objects.all().order_by("name")

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        role_name = request.POST.get("role")

        usuario = get_object_or_404(User, pk=user_id)
        usuario.groups.clear()

        if role_name:
            grupo = get_object_or_404(Group, name=role_name)
            usuario.groups.add(grupo)

        messages.success(request, f"Roles actualizados para {usuario.username}.")
        return redirect("pedidos:gestionar_usuarios")

    return render(request, "pedidos/gestionar_usuarios.html", {
        "usuarios": usuarios,
        "roles": roles,
    })


@staff_required
def cambiar_password_admin(request):
    user = request.user

    if request.method == "POST":
        form = AdminPasswordChangeForm(user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Tu contraseña se actualizó correctamente.")
            return redirect("pedidos:menu")
    else:
        form = AdminPasswordChangeForm(user)

    return render(request, "pedidos/cambiar_password_admin.html", {"form": form})


# --- [NUEVA FUNCIÓN] GESTIÓN DE CARTERA ---
@login_required
@user_passes_test(is_superuser_check) # Solo el superusuario puede tocar el dinero
def admin_ver_cartera(request, user_id):
    """
    Permite al administrador ver y modificar el saldo de un usuario específico.
    """
    usuario_objetivo = get_object_or_404(User, id=user_id)
    
    # Nos aseguramos de que tenga perfil (si no, lo creamos al vuelo para evitar errores)
    if not hasattr(usuario_objetivo, 'perfil'):
        Perfil.objects.create(user=usuario_objetivo)
    
    perfil = usuario_objetivo.perfil

    if request.method == 'POST':
        try:
            # El admin puede sumar o restar (usando números negativos)
            monto_str = request.POST.get('monto', '0')
            monto = int(monto_str)
            
            if monto != 0:
                perfil.saldo += monto
                perfil.save()
                
                accion = "añadido" if monto > 0 else "descontado"
                messages.success(request, f"Se han {accion} ${abs(monto)} a la cartera de {usuario_objetivo.username}.")
            else:
                messages.warning(request, "El monto debe ser distinto de 0.")
                
        except ValueError:
            messages.error(request, "Monto inválido. Ingresa un número entero.")
            
        # Redirigimos a la misma página para ver el saldo actualizado
        return redirect('pedidos:admin_ver_cartera', user_id=user_id)

    return render(request, 'pedidos/admin_cartera.html', {'usuario': usuario_objetivo})

@staff_required
def admin_eliminar_usuario(request, user_id):
    """
    Elimina un usuario del sistema.
    Incluye protección para no eliminarse a uno mismo.
    """
    if request.method == 'POST':
        usuario_a_borrar = get_object_or_404(User, pk=user_id)
        
        # Validación de seguridad: No te puedes borrar a ti mismo
        if usuario_a_borrar == request.user:
            messages.error(request, "No puedes eliminar tu propia cuenta desde aquí.")
        else:
            nombre = usuario_a_borrar.username
            usuario_a_borrar.delete()
            messages.success(request, f"El usuario '{nombre}' ha sido eliminado correctamente.")
            
    return redirect("pedidos:gestionar_usuarios")