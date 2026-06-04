"""
Serializers for the Infolectric API.
Converts model instances to/from JSON.
"""

from decimal import Decimal
from rest_framework import serializers
from .models import Component, Category, WireSize
from .models import ApplianceLoad


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


class ApplianceLoadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplianceLoad
        fields = ['id', 'name', 'voltage', 'power_watts', 'category', 'estimated_current', 'created_at', 'updated_at']
        read_only_fields = ['estimated_current', 'created_at', 'updated_at']


class PowerToCurrentSerializer(serializers.Serializer):
    power_watts = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    voltage = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, default=Decimal('220.00'))
    current = serializers.DecimalField(max_digits=10, decimal_places=4, required=False)
    computed_current = serializers.DecimalField(max_digits=10, decimal_places=4, read_only=True)
    adjusted_current = serializers.DecimalField(max_digits=10, decimal_places=4, read_only=True)
    recommendations = WireSizeSerializer(many=True, read_only=True)

    def validate(self, attrs):
        power = attrs.get('power_watts')
        voltage = attrs.get('voltage')
        current = attrs.get('current')

        if current is None and power is None:
            raise serializers.ValidationError('Either current or power must be provided.')

        if current is None and voltage is None:
            attrs['voltage'] = Decimal('220.00')

        return attrs


class ProjectBuilderOutputSerializer(serializers.Serializer):
    total_power_watts = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_current = serializers.DecimalField(max_digits=12, decimal_places=4)
    adjusted_current = serializers.DecimalField(max_digits=12, decimal_places=4)
    recommended_breaker = serializers.IntegerField()
    recommendations = WireSizeSerializer(many=True)
