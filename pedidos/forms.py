from django import forms
from .models import Plato
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class PlatoAdminForm(forms.ModelForm):
    imagen_archivo = forms.FileField(required=False, help_text="Sube imagen (se guarda en la BD)")
    class Meta:
        model = Plato
        fields = ['categoria', 'nombre', 'descripcion', 'precio', 'destacado']
    def save(self, commit=True):
        obj = super().save(commit=False)
        f = self.cleaned_data.get('imagen_archivo')
        if f:
            obj.imagen_bytes = f.read()
            obj.imagen_mime = getattr(f, 'content_type', 'image/jpeg')
            obj.imagen_nombre = getattr(f, 'name', '')
        if commit:
            obj.save()
        return obj


class SignupClienteForm(UserCreationForm):
    first_name = forms.CharField(label="Nombre", max_length=150)
    last_name  = forms.CharField(label="Apellido", max_length=150)
    direccion  = forms.CharField(label="Dirección", max_length=250)
    telefono   = forms.CharField(label="Teléfono", max_length=30)

    password1 = forms.CharField(
        label=("Contraseña"),
        widget=forms.PasswordInput,
        help_text=("Debe tener al menos 8 caracteres. Recomendamos usar mayúsculas, minúsculas, números y un carácter especial."),
    )
    password2 = forms.CharField(
        label=("Confirmar contraseña"),
        widget=forms.PasswordInput,
        help_text=("Ingresa la misma contraseña para verificarla.")
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "direccion", "telefono", "password1", "password2")
    
    def clean(self):
        try:
            super().clean()
        except ValidationError as e:
            
            for code, message_list in e.error_dict.items():
                
                if code == 'password_mismatch':
                    raise ValidationError(
                        "Las contraseñas ingresadas no coinciden. Por favor, verifica ambas.",
                        code='password_mismatch'
                    )
        
        return self.cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name  = self.cleaned_data["last_name"]
        if commit:
            user.save()
            perfil = user.perfil
            perfil.direccion = self.cleaned_data["direccion"]
            perfil.telefono  = self.cleaned_data["telefono"]
            perfil.save()
        return user

class LoginConRecordarmeForm(AuthenticationForm):
    remember_me = forms.BooleanField(label="Recordarme", required=False)