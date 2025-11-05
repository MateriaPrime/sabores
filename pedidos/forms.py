from django import forms
from .models import Plato
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class PlatoAdminForm(forms.ModelForm):
    imagen_archivo = forms.FileField(required=False, help_text="Sube imagen (se guarda en la BD)")
    
    class Meta:
        # --- 1. DEFINIMOS LAS VARIABLES PRIMERO ---
        tailwind_input_classes = 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm'
        tailwind_select_classes = 'w-full block px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm'
        tailwind_textarea_classes = 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm'
        tailwind_checkbox_classes = 'h-4 w-4 text-orange-600 border-gray-300 rounded focus:ring-orange-500'
        
        # --- 2. DEFINIMOS EL MODELO Y LOS CAMPOS ---
        model = Plato
        fields = ['categoria', 'nombre', 'descripcion', 'precio', 'destacado']
        
        # --- 3. AHORA USAMOS LAS VARIABLES (SIN COMILLAS) ---
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
    # Define las clases de Tailwind que usaremos en todos los campos
    tailwind_input_classes = 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm'
    
    # Sobrescribimos los campos para agregar los widgets
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
        # Le decimos al campo 'username' que también use el widget con las clases
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
    remember_me = forms.BooleanField(label="Recordarme", required=False)