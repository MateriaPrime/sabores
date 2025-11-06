from django import forms
from .models import Plato
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Plato, Perfil
from django.core.validators import RegexValidator 

# =========================================================================
# VALIDADOR DE TELÉFONO (CORREGIDO: Fuerza el signo '+' inicial)
# =========================================================================
telefono_validator = RegexValidator(
    # La nueva regla: ^ (inicio) \+ (debe ser un signo más) [0-9]+ (seguido de uno o más dígitos) $ (fin)
    regex=r'^\+[0-9]+$',
    message="El número de teléfono debe comenzar con '+' y solo puede contener números después.",
    code='invalid_phone_number'
)

class PlatoAdminForm(forms.ModelForm):
    imagen_archivo = forms.FileField(required=False, help_text="Sube imagen (se guarda en la BD)")
    
    class Meta:
        # Definimos las variables de clases de Tailwind A DENTRO de Meta
        tailwind_input_classes = 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm'
        tailwind_select_classes = 'w-full block px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm'
        tailwind_textarea_classes = 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm'
        tailwind_checkbox_classes = 'h-4 w-4 text-orange-600 border-gray-300 rounded focus:ring-orange-500'
        
        model = Plato
        fields = ['categoria', 'nombre', 'descripcion', 'precio', 'destacado']
        
        widgets = {
            'categoria': forms.Select(attrs={'class': tailwind_select_classes}),
            'nombre': forms.TextInput(attrs={'class': tailwind_input_classes}),
            'descripcion': forms.Textarea(attrs={'class': tailwind_textarea_classes, 'rows': 4}),
            'precio': forms.NumberInput(attrs={'class': tailwind_input_classes}),
            'destacado': forms.CheckboxInput(attrs={'class': tailwind_checkbox_classes}),
        }

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
    tailwind_input_classes = 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm'
    
    first_name = forms.CharField(
        label="Nombre", 
        max_length=150,
        widget=forms.TextInput(attrs={'class': tailwind_input_classes})
    )
    last_name  = forms.CharField(
        label="Apellido", 
        max_length=150,
        widget=forms.TextInput(attrs={'class': tailwind_input_classes})
    )
    direccion  = forms.CharField(
        label="Dirección", 
        max_length=250,
        widget=forms.TextInput(attrs={'class': tailwind_input_classes})
    )
    telefono   = forms.CharField(
        label="Teléfono", 
        max_length=30,
        validators=[telefono_validator], 
        widget=forms.TextInput(attrs={'class': tailwind_input_classes})
    )

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
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm'})
        }
    
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
    tailwind_input_classes = 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm'
    tailwind_checkbox_classes = 'h-4 w-4 text-orange-600 border-gray-300 rounded focus:ring-orange-500'

    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(attrs={
            'class': tailwind_input_classes,
            'placeholder': 'tu-usuario'
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': tailwind_input_classes,
            'placeholder': '••••••••'
        })
    )
    remember_me = forms.BooleanField(
        label="Recordarme", 
        required=False,
        widget=forms.CheckboxInput(attrs={'class': tailwind_checkbox_classes})
    )


class SignupRepartidorForm(UserCreationForm):
    
    tailwind_input_classes = 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm'
    
    first_name = forms.CharField(
        label="Nombre", 
        max_length=150,
        widget=forms.TextInput(attrs={'class': tailwind_input_classes})
    )
    last_name  = forms.CharField(
        label="Apellido", 
        max_length=150,
        widget=forms.TextInput(attrs={'class': tailwind_input_classes})
    )
    telefono   = forms.CharField(
        label="Teléfono", 
        max_length=30,
        validators=[telefono_validator], 
        widget=forms.TextInput(attrs={'class': tailwind_input_classes})
    )

    password1 = forms.CharField(
        label="Contraseña",
        help_text="Debe tener al menos 8 caracteres.",
        widget=forms.PasswordInput(attrs={'class': tailwind_input_classes})
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'class': tailwind_input_classes})
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "telefono", "password1", "password2")
        
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm'})
        }
    
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
            perfil.telefono  = self.cleaned_data["telefono"]
            perfil.save()
        return user
    
class PerfilUpdateForm(forms.ModelForm):
    tailwind_input_classes = 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm'

    first_name = forms.CharField(
        label="Nombre", 
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': tailwind_input_classes})
    )
    last_name  = forms.CharField(
        label="Apellido", 
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': tailwind_input_classes})
    )
    
    direccion  = forms.CharField(
        label="Dirección", 
        max_length=250,
        widget=forms.TextInput(attrs={'class': tailwind_input_classes})
    )
    telefono   = forms.CharField(
        label="Teléfono", 
        max_length=30,
        validators=[telefono_validator],
        widget=forms.TextInput(attrs={'class': tailwind_input_classes})
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and hasattr(self.instance, 'perfil'):
            self.initial['direccion'] = self.instance.perfil.direccion
            self.initial['telefono'] = self.instance.perfil.telefono

    def save(self, commit=True):
        user = super().save(commit=True)
        
        perfil = user.perfil
        perfil.direccion = self.cleaned_data['direccion']
        perfil.telefono = self.cleaned_data['telefono']
        perfil.save()
        return user