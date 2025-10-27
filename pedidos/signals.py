# pedidos/signals.py
from django.db.models.signals import post_migrate, post_save
from django.contrib.auth.models import User, Group
from django.dispatch import receiver
from .models import Perfil

@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)

@receiver(post_migrate)
def ensure_groups(sender, **kwargs):
    for name in ['CLIENTE', 'REPARTIDOR']:
        Group.objects.get_or_create(name=name)