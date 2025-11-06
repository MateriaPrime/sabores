# pedidos/urls.py
from django.urls import path
from . import views
from . import views, views_auth, views_roles

app_name = 'pedidos'

urlpatterns = [
    path('', views.home, name='home'),
    path('menu/', views.menu, name='menu'),
    path('cart/', views.cart, name='cart'),
    path('add/<int:plato_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove/<int:plato_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('orden/<int:pedido_id>/', views.order_detail, name='order_detail'),
    path('img/plato/<int:pk>/', views.plato_imagen, name='plato_imagen'),
    path('mi-cuenta/', views_roles.dash_cliente, name='dash_cliente'),
    path('repartidor/', views_roles.dash_repartidor, name='dash_repartidor'),
    path('mi-cuenta/', views_roles.dash_cliente, name='dash_cliente'),
    path('mi-cuenta/editar/', views_roles.perfil_editar, name='perfil_editar'),
    path('mi-cuenta/eliminar/', views_roles.perfil_eliminar_confirmar, name='perfil_eliminar_confirmar'),
    path('repartidor/', views_roles.dash_repartidor, name='dash_repartidor'),
    path('signup/cliente/', views_roles.signup_cliente, name='signup_cliente'),
    path('plato/crear/', views_roles.plato_crear, name='plato_crear'),
    path('plato/editar/<int:pk>/', views_roles.plato_editar, name='plato_editar'),
    path('plato/eliminar/<int:pk>/', views_roles.plato_eliminar, name='plato_eliminar'),
    path('signup/repartidor/', views_roles.signup_repartidor, name='signup_repartidor'),
    path('repartidor/aceptar/<int:pedido_id>/', views_roles.pedido_aceptar, name='pedido_aceptar'),
    path('repartidor/entregado/<int:pedido_id>/', views_roles.pedido_entregado, name='pedido_entregado'),
]
