# pedidos/context_processors.py

def cart_total_items(request):
    """
    (Esta es la función que ya tenías para el carrito)
    """
    cart = request.session.get('cart', {})
    total_count = 0
    for cantidad in cart.values():
        total_count += cantidad
    return {'cart_total_items': total_count}

# --- [INICIO] NUEVA FUNCIÓN ---
def user_context(request):
    """
    Devuelve una variable 'is_cliente' si el usuario NO es admin ni repartidor.
    """
    is_cliente = False
    if request.user.is_authenticated:
        is_repartidor = request.user.groups.filter(name='REPARTIDOR').exists()
        is_admin = request.user.is_staff or request.user.is_superuser
        
        # Es cliente si no es ni admin ni repartidor
        is_cliente = not is_repartidor and not is_admin
        
    return {'is_cliente': is_cliente}
# --- [FIN] NUEVA FUNCIÓN ---