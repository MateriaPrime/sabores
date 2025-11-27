"""
URL configuration for sabores project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from pedidos import views_auth

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('pedidos.urls')),

    path('login/', views_auth.SaboresLoginView.as_view(), name='login'),
    path('logout/', views_auth.logout_view, name='logout'),
    path('dashboard/', views_auth.dashboard_router, name='dashboard_router'),

    # password reset
    path('password-reset/', views_auth.ResetPasswordView.as_view(), name='password_reset'),
    path('password-reset/done/', views_auth.ResetPasswordDoneView.as_view(), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', views_auth.ResetPasswordConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', views_auth.ResetPasswordCompleteView.as_view(), name='password_reset_complete'),
]