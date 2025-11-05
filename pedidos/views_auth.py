from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView, PasswordResetDoneView, PasswordResetCompleteView
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from .forms import LoginConRecordarmeForm

class SaboresLoginView(LoginView):
    template_name = 'pedidos/login.html'
    authentication_form = LoginConRecordarmeForm

    def form_valid(self, form):
        # maneja "recordarme": sesión expira al cerrar navegador si NO tildan
        response = super().form_valid(form)
        remember = form.cleaned_data.get('remember_me')
        if remember:
            # 2 semanas
            self.request.session.set_expiry(60 * 60 * 24 * 14)
        else:
            self.request.session.set_expiry(0)  # expira al cerrar navegador
        return response

def logout_view(request):
    logout(request)
    messages.success(request, "Sesión cerrada.")
    return redirect('pedidos:home')

def dashboard_router(request):
    if not request.user.is_authenticated:
        return redirect('login')
    u = request.user
    if u.is_superuser or u.is_staff:
        return redirect('pedidos:menu') # Redirige al menú principal
    if u.groups.filter(name='REPARTIDOR').exists():
        return redirect(reverse('pedidos:dash_repartidor'))
    return redirect(reverse('pedidos:dash_cliente'))

# Password reset (olvidé mi contraseña)
class ResetPasswordView(PasswordResetView):
    template_name = 'pedidos/password_reset.html'
    email_template_name = 'pedidos/password_reset_email.txt'
    subject_template_name = 'pedidos/password_reset_subject.txt'
    success_url = '/password-reset/done/'

class ResetPasswordDoneView(PasswordResetDoneView):
    template_name = 'pedidos/password_reset_done.html'

class ResetPasswordConfirmView(PasswordResetConfirmView):
    template_name = 'pedidos/password_reset_confirm.html'
    success_url = '/password-reset/complete/'

class ResetPasswordCompleteView(PasswordResetCompleteView):
    template_name = 'pedidos/password_reset_complete.html'
