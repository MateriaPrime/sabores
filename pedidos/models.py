from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(max_length=60)
    class Meta:
        verbose_name_plural = 'Categorías'
    def __str__(self): return self.nombre

class Plato(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='platos')
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    precio = models.IntegerField(help_text='Precio en CLP (sin puntos)')

    # ===== NUEVO: imagen guardada en la BD =====
    imagen_bytes = models.BinaryField(blank=True, null=True)
    imagen_mime  = models.CharField(max_length=50, default='image/jpeg')
    imagen_nombre = models.CharField(max_length=255, blank=True, null=True)
    
    destacado = models.BooleanField(default=False)
    def __str__(self): return self.nombre

class Pedido(models.Model):
    ESTADOS = [('PREP','Preparando'), ('CAM','En camino'), ('ENT','Entregado')]
    nombre = models.CharField(max_length=120)
    telefono = models.CharField(max_length=30)
    direccion = models.CharField(max_length=250)
    creado = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=4, choices=ESTADOS, default='PREP')
    estimado_min = models.PositiveIntegerField(default=30)
    estimado_max = models.PositiveIntegerField(default=45)
    def total(self): return sum(item.subtotal() for item in self.items.all())
    def __str__(self): return f'Pedido #{self.id} - {self.nombre}'

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    plato = models.ForeignKey(Plato, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.IntegerField()
    def subtotal(self): return self.cantidad * self.precio_unitario
