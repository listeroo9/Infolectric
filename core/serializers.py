"""
Serializers for the Infolectric API.
Converts model instances to/from JSON.
"""

from rest_framework import serializers
from .models import Component, Category, WireSize


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    components_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'components_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_components_count(self, obj):
        """Get count of components in this category."""
        return obj.components.count()


class ComponentSerializer(serializers.ModelSerializer):
    """Serializer for Component model."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Component
        fields = ['id', 'name', 'description', 'category', 'category_name', 
                  'image', 'image_url', 'date_created', 'updated_at']
        read_only_fields = ['date_created', 'updated_at']

    def get_image_url(self, obj):
        """Get absolute URL for component image."""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None


class WireSizeSerializer(serializers.ModelSerializer):
    """Serializer for WireSize model."""
    class Meta:
        model = WireSize
        fields = ['id', 'wire_size_mm2', 'max_ampacity', 'description', 
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class WireRecommendationSerializer(serializers.Serializer):
    """Serializer for wire recommendation calculator request/response."""
    required_current = serializers.DecimalField(max_digits=6, decimal_places=2)
    recommendations = WireSizeSerializer(many=True, read_only=True)
