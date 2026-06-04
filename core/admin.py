"""
Django Admin configuration for Infolectric.
Register models for admin interface.
"""

from django.contrib import admin
from .models import Component, Category, WireSize


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for Category model."""
    list_display = ['name', 'created_at', 'component_count']
    search_fields = ['name', 'description']
    ordering = ['name']

    def component_count(self, obj):
        """Display count of components in category."""
        return obj.components.count()
    component_count.short_description = 'Components'


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    """Admin interface for Component model."""
    list_display = ['name', 'category', 'date_created', 'updated_at']
    list_filter = ['category', 'date_created']
    search_fields = ['name', 'description']
    readonly_fields = ['date_created', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category')
        }),
        ('Details', {
            'fields': ('description', 'image')
        }),
        ('Timestamps', {
            'fields': ('date_created', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WireSize)
class WireSizeAdmin(admin.ModelAdmin):
    """Admin interface for WireSize model."""
    list_display = ['wire_size_mm2', 'max_ampacity', 'created_at']
    list_filter = ['max_ampacity', 'created_at']
    search_fields = ['description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['wire_size_mm2']
    fieldsets = (
        ('Wire Specifications', {
            'fields': ('wire_size_mm2', 'max_ampacity')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
