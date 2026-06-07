"""
Django Admin configuration for Infolectric.
Register models for admin interface.
"""

from django.contrib import admin
from .models import Component, Category, WireSize, ChangeRequest
from .models import ApplianceLoad


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


@admin.register(ApplianceLoad)
class ApplianceLoadAdmin(admin.ModelAdmin):
    """Admin for ApplianceLoad model."""
    list_display = ['name', 'power_watts', 'voltage', 'estimated_current', 'category', 'created_at']
    search_fields = ['name', 'category__name']
    list_filter = ['voltage', 'category']
    readonly_fields = ['estimated_current', 'created_at', 'updated_at']
    ordering = ['name']
    fieldsets = (
        ('Basic', {'fields': ('name', 'category')}),
        ('Specs', {'fields': ('power_watts', 'voltage', 'estimated_current')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(ChangeRequest)
class ChangeRequestAdmin(admin.ModelAdmin):
    """Admin interface for user change requests."""
    list_display = ['title', 'request_type', 'target_model', 'status', 'user', 'created_at']
    list_filter = ['status', 'request_type', 'target_model', 'created_at']
    search_fields = ['title', 'reason', 'admin_notes', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'approved_at', 'rejected_at', 'cancelled_at']
    ordering = ['-created_at']
    fieldsets = (
        ('Request Information', {
            'fields': ('request_type', 'target_model', 'target_object_id', 'title', 'reason')
        }),
        ('User & Status', {
            'fields': ('user', 'status', 'approved_by', 'approved_at', 'rejected_by', 'rejected_at', 'cancelled_at')
        }),
        ('Admin Notes & Payload', {
            'fields': ('admin_notes', 'payload')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
