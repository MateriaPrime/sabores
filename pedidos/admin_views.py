# pedidos/admin_views.py
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

def staff_required(view_func):
    return user_passes_test(lambda u: u.is_staff)(view_func)

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
            return redirect("pedidos:menu")   # o la vista principal que tengas
    else:
        form = AdminPasswordChangeForm(user)

    return render(request, "pedidos/cambiar_password_admin.html", {"form": form})
