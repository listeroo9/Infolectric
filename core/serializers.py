"""
Serializers for the Infolectric API.
Converts model instances to/from JSON.
"""

from decimal import Decimal
from rest_framework import serializers
from .models import Component, Category, WireSize
from .models import ApplianceLoad
from . import services


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
    required_current = serializers.DecimalField(max_digits=10, decimal_places=4)
    usage_type = serializers.ChoiceField(
        choices=services.USAGE_TYPE_CHOICES,
        required=False,
        default=services.USAGE_TYPE_NORMAL_HOUSEHOLD
    )
    wire_length = serializers.DecimalField(required=False, max_digits=10, decimal_places=2, default=Decimal('10.00'))
    wire_resistance = serializers.DecimalField(max_digits=12, decimal_places=6, read_only=True)
    voltage_drop = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    voltage_drop_percent = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    power_loss = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    efficiency = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    safety_factor = serializers.DecimalField(max_digits=4, decimal_places=2, read_only=True)
    usable_current = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    usable_power = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    recommendations = WireSizeSerializer(many=True, read_only=True)


class WireExplorerRequestSerializer(serializers.Serializer):
    wire_size_id = serializers.IntegerField()
    usage_type = serializers.ChoiceField(
        choices=services.USAGE_TYPE_CHOICES,
        required=False,
        default=services.USAGE_TYPE_NORMAL_HOUSEHOLD
    )
    wire_length = serializers.DecimalField(required=False, max_digits=10, decimal_places=2, default=Decimal('10.00'))


class WireExplorerApplianceSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = ApplianceLoad
        fields = ['id', 'name', 'category', 'power_watts', 'voltage', 'estimated_current']
        read_only_fields = ['id', 'name', 'category', 'power_watts', 'voltage', 'estimated_current']


class WireExplorerCombinationApplianceSerializer(serializers.Serializer):
    name = serializers.CharField()
    power_watts = serializers.DecimalField(max_digits=10, decimal_places=2)
    voltage = serializers.DecimalField(max_digits=8, decimal_places=2)
    current_amps = serializers.DecimalField(max_digits=10, decimal_places=2)
    contribution_percent = serializers.DecimalField(max_digits=5, decimal_places=1)


class WireExplorerCombinationSerializer(serializers.Serializer):
    appliances = WireExplorerCombinationApplianceSerializer(many=True)
    device_count = serializers.IntegerField()
    total_current = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_power = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_voltage = serializers.DecimalField(max_digits=8, decimal_places=2)
    utilization = serializers.DecimalField(max_digits=5, decimal_places=1)
    wire_limit = serializers.DecimalField(max_digits=10, decimal_places=2)
    usable_limit = serializers.DecimalField(max_digits=10, decimal_places=2)
    level = serializers.IntegerField()
    level_label = serializers.CharField()
    level_description = serializers.CharField()
    is_safe = serializers.BooleanField()


class WireExplorerSerializer(serializers.Serializer):
    wire_size = serializers.CharField()
    max_ampacity = serializers.IntegerField()
    usage_type = serializers.CharField()
    usage_label = serializers.CharField()
    usage_badge = serializers.CharField()
    safety_factor = serializers.DecimalField(max_digits=4, decimal_places=2)
    usable_current = serializers.DecimalField(max_digits=10, decimal_places=2)
    usable_power = serializers.DecimalField(max_digits=12, decimal_places=2)
    max_power_theoretical = serializers.DecimalField(max_digits=12, decimal_places=2)
    recommended_max_power = serializers.DecimalField(max_digits=12, decimal_places=2)
    wire_length = serializers.DecimalField(max_digits=10, decimal_places=2)
    wire_resistance = serializers.DecimalField(max_digits=12, decimal_places=6)
    voltage_drop = serializers.DecimalField(max_digits=10, decimal_places=2)
    voltage_drop_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    power_loss = serializers.DecimalField(max_digits=12, decimal_places=2)
    efficiency = serializers.DecimalField(max_digits=6, decimal_places=2)
    warning = serializers.DictField(child=serializers.CharField())
    compatible_appliances = WireExplorerApplianceSerializer(many=True)
    safe_combinations = WireExplorerCombinationSerializer(many=True)


class ApplianceLoadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplianceLoad
        fields = ['id', 'name', 'voltage', 'power_watts', 'category', 'estimated_current', 'created_at', 'updated_at']
        read_only_fields = ['estimated_current', 'created_at', 'updated_at']


class PowerToCurrentSerializer(serializers.Serializer):
    power_watts = serializers.DecimalField(required=False, max_digits=10, decimal_places=2)
    voltage = serializers.DecimalField(required=False, max_digits=8, decimal_places=2, default=Decimal('220.00'))
    current = serializers.DecimalField(required=False, max_digits=10, decimal_places=4)
    usage_type = serializers.ChoiceField(
        choices=services.USAGE_TYPE_CHOICES,
        required=False,
        default=services.USAGE_TYPE_NORMAL_HOUSEHOLD
    )
    wire_length = serializers.DecimalField(required=False, max_digits=10, decimal_places=2, default=Decimal('10.00'))
    computed_current = serializers.DecimalField(max_digits=10, decimal_places=4, read_only=True)
    adjusted_current = serializers.DecimalField(max_digits=10, decimal_places=4, read_only=True)
    wire_resistance = serializers.DecimalField(max_digits=12, decimal_places=6, read_only=True)
    voltage_drop = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    voltage_drop_percent = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    power_loss = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    efficiency = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    safety_factor = serializers.DecimalField(max_digits=4, decimal_places=2, read_only=True)
    usable_current = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    usable_power = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    recommendations = WireSizeSerializer(many=True, read_only=True)

    def validate(self, attrs):
        power = attrs.get('power_watts')
        voltage = attrs.get('voltage')
        current = attrs.get('current')

        if current is None and power is None:
            raise serializers.ValidationError('Either current or power must be provided.')

        if current is None and voltage is None:
            attrs['voltage'] = Decimal('220.00')

        if attrs.get('wire_length') is None:
            attrs['wire_length'] = Decimal('10.00')

        return attrs


class ProjectBuilderOutputSerializer(serializers.Serializer):
    total_power_watts = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_current = serializers.DecimalField(max_digits=12, decimal_places=4)
    adjusted_current = serializers.DecimalField(max_digits=12, decimal_places=4)
    recommended_breaker = serializers.IntegerField()
    recommendations = WireSizeSerializer(many=True)
