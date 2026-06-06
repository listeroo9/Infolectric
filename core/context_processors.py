def management_permissions(request):
    """Add management permission flags to every template context."""
    user = request.user
    can_manage = user.is_authenticated and (user.is_staff or user.is_superuser)

    return {
        'is_content_manager': can_manage,
        'can_manage_components': can_manage,
        'can_manage_appliances': can_manage,
        'can_manage_categories': can_manage,
        'can_manage_wires': can_manage,
    }
