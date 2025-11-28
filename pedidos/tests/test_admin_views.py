import pytest
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.contrib.messages import get_messages
from pedidos.models import Perfil

@pytest.mark.django_db
class TestAdminViews:
    
    @pytest.fixture
    def superuser(self, client):
        user = User.objects.create_superuser('admin', 'admin@test.com', 'password123')
        # Corrección 1: Usar get_or_create para el perfil
        perfil, created = Perfil.objects.get_or_create(user=user)
        perfil.saldo = 0
        perfil.save()
        
        client.login(username='admin', password='password123')
        return user

    @pytest.fixture
    def staff_user(self, client):
        user = User.objects.create_user('staff', 'staff@test.com', 'password123')
        user.is_staff = True
        user.save()
        # Corrección 1: Usar get_or_create para el perfil
        Perfil.objects.get_or_create(user=user)
        
        client.login(username='staff', password='password123')
        return user

    @pytest.fixture
    def normal_user(self):
        user = User.objects.create_user('cliente', 'cliente@test.com', 'password123')
        # Corrección 1: Usar get_or_create para el perfil
        perfil, created = Perfil.objects.get_or_create(user=user)
        perfil.saldo = 1000
        perfil.save()
        return user

    # --- TEST DE CARTERA (Solo Superusuario) ---
    
    def test_admin_ver_cartera_suma_saldo(self, client, superuser, normal_user):
        url = reverse('pedidos:admin_ver_cartera', args=[normal_user.id])
        data = {'monto': '5000'}
        
        response = client.post(url, data)
        
        normal_user.perfil.refresh_from_db()
        assert normal_user.perfil.saldo == 6000
        assert response.status_code == 302

    def test_staff_no_puede_ver_cartera(self, client, staff_user, normal_user):
        url = reverse('pedidos:admin_ver_cartera', args=[normal_user.id])
        response = client.get(url)
        assert response.status_code == 302 

    # --- TEST DE GESTIÓN DE USUARIOS ---

    def test_gestionar_usuarios_cambio_rol(self, client, superuser, normal_user):
        """Prueba asignar el grupo 'Repartidor' a un usuario"""
        # CORRECCIÓN 2 (NUEVA): Usamos get_or_create para evitar el error de duplicado
        grupo_repartidor, created = Group.objects.get_or_create(name='Repartidor')
        
        url = reverse('pedidos:gestionar_usuarios')
        
        data = {
            'user_id': normal_user.id,
            'role': 'Repartidor'
        }
        
        client.post(url, data)
        assert normal_user.groups.filter(name='Repartidor').exists()

    # --- TEST DE ELIMINACIÓN DE USUARIOS ---

    def test_admin_eliminar_usuario(self, client, superuser, normal_user):
        url = reverse('pedidos:admin_eliminar_usuario', args=[normal_user.id])
        client.post(url)
        assert not User.objects.filter(id=normal_user.id).exists()

    def test_admin_no_puede_auto_eliminarse(self, client, superuser):
        url = reverse('pedidos:admin_eliminar_usuario', args=[superuser.id])
        response = client.post(url)
        
        assert User.objects.filter(id=superuser.id).exists()
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) > 0
        assert "No puedes eliminar tu propia cuenta" in str(messages[0])