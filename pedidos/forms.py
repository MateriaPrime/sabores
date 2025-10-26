from django import forms
from .models import Plato

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