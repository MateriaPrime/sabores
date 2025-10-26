from django.contrib import admin
from .models import Categoria, Plato, Pedido, ItemPedido
from .forms import PlatoAdminForm

@admin.register(Plato)
class PlatoAdmin(admin.ModelAdmin):
    form = PlatoAdminForm
    list_display = ('nombre','categoria','precio','destacado')

admin.site.register(Categoria)

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    inlines = [ItemPedidoInline]
    list_display = ('id', 'nombre', 'telefono', 'estado', 'creado')
