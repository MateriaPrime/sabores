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
    path('signup/cliente/', views_roles.signup_cliente, name='signup_cliente'),
]
