"""
API views for the Infolectric application.
RESTful API endpoints for components, categories, wire sizes, and calculator.
"""

from decimal import Decimal
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .models import Component, Category, WireSize, ApplianceLoad
from .serializers import (
    ComponentSerializer, CategorySerializer, WireSizeSerializer,
    WireRecommendationSerializer, ApplianceLoadSerializer,
    PowerToCurrentSerializer, ProjectBuilderOutputSerializer,
    WireExplorerRequestSerializer, WireExplorerSerializer
)
from . import services


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for categories.
    
    Supports:
    - GET /api/categories/ - List all categories
    - POST /api/categories/ - Create a new category
    - GET /api/categories/{id}/ - Retrieve a specific category
    - PUT /api/categories/{id}/ - Update a category
    - DELETE /api/categories/{id}/ - Delete a category
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def components(self, request, pk=None):
        """Get all components in a specific category."""
        category = self.get_object()
        components = category.components.all()
        serializer = ComponentSerializer(components, many=True, context={'request': request})
        return Response(serializer.data)


class ComponentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for components.
    
    Supports:
    - GET /api/components/ - List all components (with search and filtering)
    - POST /api/components/ - Create a new component
    - GET /api/components/{id}/ - Retrieve a specific component
    - PUT /api/components/{id}/ - Update a component
    - DELETE /api/components/{id}/ - Delete a component
    """
    queryset = Component.objects.all()
    serializer_class = ComponentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'date_created']
    ordering = ['-date_created']

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get components filtered by category."""
        category_id = request.query_params.get('category_id')
        if not category_id:
            return Response(
                {'error': 'category_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        components = Component.objects.filter(category_id=category_id)
        serializer = self.get_serializer(components, many=True)
        return Response(serializer.data)


class WireSizeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for wire sizes.
    
    Supports:
    - GET /api/wire-sizes/ - List all wire sizes
    - POST /api/wire-sizes/ - Create a new wire size
    - GET /api/wire-sizes/{id}/ - Retrieve a specific wire size
    - PUT /api/wire-sizes/{id}/ - Update a wire size
    - DELETE /api/wire-sizes/{id}/ - Delete a wire size
    """
    queryset = WireSize.objects.all()
    serializer_class = WireSizeSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['wire_size_mm2', 'max_ampacity']
    ordering = ['wire_size_mm2']


class WireRecommendationViewSet(viewsets.ViewSet):
    """
    API endpoint for wire recommendations.
    
    Supports:
    - POST /api/wire-recommendation/ - Get recommended wire sizes for a given current
    """

    @action(detail=False, methods=['post'])
    def recommend(self, request):
        """
        Recommend wire sizes based on required current.
        
        Request body:
        {
            "required_current": 10.5,
            "wire_length": 10
        }
        
        Response:
        {
            "required_current": 10.5,
            "wire_length": 10,
            "voltage_drop": 3.2,
            "voltage_drop_percent": 1.45,
            "power_loss": 12.6,
            "efficiency": 98.5,
            "recommendations": [ ... ]
        }
        """
        serializer = WireRecommendationSerializer(data=request.data)
        if serializer.is_valid():
            required_current = Decimal(serializer.validated_data['required_current'])
            usage_type = serializer.validated_data.get('usage_type', services.USAGE_TYPE_NORMAL_HOUSEHOLD)
            wire_length = serializer.validated_data.get('wire_length', Decimal('10.00'))
            adjusted_current = services.adjusted_current_for_safety(required_current)

            wire_sizes = WireSize.objects.filter(
                max_ampacity__gte=adjusted_current
            ).order_by('wire_size_mm2')

            if not wire_sizes.exists():
                return Response(
                    {
                        'error': f'No wire sizes available for adjusted current {adjusted_current}A',
                        'required_current': required_current,
                        'adjusted_current': adjusted_current,
                        'recommendations': []
                    },
                    status=status.HTTP_404_NOT_FOUND
                )


                # Use service to build formatted recommendations and capability numbers
                recommendations = services.recommend_wires_for_current(required_current)
                # pick first for summary metrics
                first = recommendations[0]
                selected_wire_size = Decimal(first['wire_size_mm2'])
                resistance = services.calculate_wire_resistance(selected_wire_size, wire_length)
                vdrop = services.calculate_voltage_drop(required_current, resistance)
                voltage_drop = services.format_decimal(vdrop, 3)
                voltage_drop_percent = services.format_decimal(services.calculate_voltage_drop_percent(Decimal('220'), vdrop), 2)
                power_loss = services.format_decimal(services.calculate_power_loss(required_current, resistance), 2)
                efficiency = services.format_decimal(services.calculate_efficiency(Decimal('220'), vdrop), 2)
                usable_current = services.calculate_usable_current(Decimal(first['max_ampacity']), usage_type)
                usable_power = services.format_decimal(services.calculate_usable_power(Decimal('220'), usable_current), 2)

                return Response({
                    'required_current': services.format_decimal(required_current, 3),
                    'usage_type': usage_type,
                    'safety_factor': services.format_decimal(safety_factor, 2),
                    'adjusted_current': services.format_decimal(adjusted_current, 3),
                    'usable_current': services.format_decimal(usable_current, 2),
                    'usable_power': usable_power,
                    'wire_length': services.format_decimal(wire_length, 2),
                    'voltage_drop': voltage_drop,
                    'voltage_drop_percent': voltage_drop_percent,
                    'power_loss': power_loss,
                    'efficiency': efficiency,
                    'recommendations': recommendations
                })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ApplianceLoadViewSet(viewsets.ModelViewSet):
    """API endpoint for ApplianceLoad CRUD."""
    queryset = ApplianceLoad.objects.all()
    serializer_class = ApplianceLoadSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'category__name']
    ordering_fields = ['name', 'power_watts']


class PowerCalcViewSet(viewsets.ViewSet):
    """API endpoint to convert power->current and recommend wires."""

    @action(detail=False, methods=['post'])
    def power_to_current(self, request):
        serializer = PowerToCurrentSerializer(data=request.data)
        if serializer.is_valid():
            power = serializer.validated_data.get('power_watts')
            voltage = serializer.validated_data.get('voltage')
            current = serializer.validated_data.get('current')
            wire_length = serializer.validated_data.get('wire_length', Decimal('10.00'))
            try:
                calculated_current = services.calculate_current(
                    power_watts=power,
                    voltage=voltage,
                    current=current
                )
            except ValueError as exc:
                return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

            usage_type = serializer.validated_data.get('usage_type', services.USAGE_TYPE_NORMAL_HOUSEHOLD)
            adjusted_current = services.adjusted_current_for_safety(calculated_current)
            recommendations = services.recommend_wires_for_current(calculated_current)
            wire_resistance = None
            voltage_drop = None
            voltage_drop_percent = None
            power_loss = None
            efficiency = None
            usable_current = None
            usable_power = None
            safety_factor = services.get_safety_factor(usage_type)

            if recommendations:
                first_wire = Decimal(recommendations[0]['wire_size_mm2'])
                wire_resistance = services.calculate_wire_resistance(first_wire, wire_length)
                vdrop = services.calculate_voltage_drop(calculated_current, wire_resistance)
                voltage_drop = vdrop.quantize(Decimal('0.01'))
                voltage_drop_percent = services.calculate_voltage_drop_percent(voltage or Decimal('220'), vdrop).quantize(Decimal('0.01'))
                power_loss = services.calculate_power_loss(calculated_current, wire_resistance).quantize(Decimal('0.01'))
                efficiency = services.calculate_efficiency(voltage or Decimal('220'), vdrop).quantize(Decimal('0.01'))
                usable_current = services.calculate_usable_current(Decimal(recommendations[0]['max_ampacity']), usage_type)
                usable_power = services.calculate_usable_power(voltage or Decimal('220'), usable_current)

            out = {
                'power_watts': services.format_decimal(services.to_decimal(power) if power is not None else Decimal('0'), 2) if power is not None else None,
                'voltage': services.format_decimal(services.to_decimal(voltage) if voltage is not None else Decimal('220'), 2),
                'current': services.format_decimal(services.to_decimal(current) if current is not None else None, 3) if current is not None else None,
                'usage_type': usage_type,
                'safety_factor': services.format_decimal(safety_factor, 2),
                'wire_length': services.format_decimal(wire_length, 2),
                'computed_current': services.format_decimal(calculated_current, 3),
                'adjusted_current': services.format_decimal(adjusted_current, 3),
                'usable_current': services.format_decimal(usable_current, 2) if usable_current is not None else None,
                'usable_power': services.format_decimal(usable_power, 2) if usable_power is not None else None,
                'wire_resistance': services.format_decimal(wire_resistance, 5) if wire_resistance is not None else None,
                'voltage_drop': voltage_drop,
                'voltage_drop_percent': voltage_drop_percent,
                'power_loss': power_loss,
                'efficiency': efficiency,
                'recommendations': recommendations,
            }
            return Response(out)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WireExplorerViewSet(viewsets.ViewSet):
    """API endpoint for wire explorer capability and safe appliance matching."""

    def create(self, request):
        serializer = WireExplorerRequestSerializer(data=request.data)
        if serializer.is_valid():
            wire_size_id = serializer.validated_data['wire_size_id']
            usage_type = serializer.validated_data.get('usage_type', services.USAGE_TYPE_NORMAL_HOUSEHOLD)
            wire_length = serializer.validated_data.get('wire_length', Decimal('10.00'))
            wire_size = get_object_or_404(WireSize, pk=wire_size_id)
            capability = services.get_wire_capability(
                wire_size=wire_size,
                wire_length=wire_length,
                usage_type=usage_type
            )
            compatible_appliances = services.get_compatible_appliances(wire_size, usage_type=usage_type)
            safe_combinations = services.generate_safe_combinations(wire_size, usage_type=usage_type)

            response_data = {
                'wire_size': capability['wire_size_mm2'],
                'max_ampacity': capability['max_ampacity'],
                'usage_type': capability['usage_type'],
                'usage_label': capability['usage_label'],
                'usage_badge': capability['usage_badge'],
                'safety_factor': capability['safety_factor'],
                'usable_current': capability['usable_current'],
                'usable_power': capability['usable_power'],
                'max_power_theoretical': capability['max_power_theoretical'],
                'recommended_max_power': capability['recommended_max_power'],
                'wire_length': capability['wire_length'],
                'wire_resistance': capability['resistance'],
                'voltage_drop': capability['voltage_drop'],
                'voltage_drop_percent': capability['voltage_drop_percent'],
                'power_loss': capability['power_loss'],
                'efficiency': capability['efficiency'],
                'warning': capability['warning'],
                'compatible_appliances': compatible_appliances,
                'safe_combinations': safe_combinations,
            }
            output_serializer = WireExplorerSerializer(response_data)
            return Response(output_serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectBuilderViewSet(viewsets.ViewSet):
    """API endpoint to build a project from selected appliances and get recommendations."""

    @action(detail=False, methods=['post'])
    def build(self, request):
        # Expect list of appliance IDs
        ids = request.data.get('appliance_ids', [])
        if not isinstance(ids, list) or not ids:
            return Response({'error': 'appliance_ids must be a non-empty list of IDs'}, status=status.HTTP_400_BAD_REQUEST)

        appliances = ApplianceLoad.objects.filter(id__in=ids)
        if not appliances.exists():
            return Response({'error': 'No appliances found for given ids'}, status=status.HTTP_404_NOT_FOUND)

        total_power = sum((services.to_decimal(a.power_watts or 0) for a in appliances), Decimal('0'))
        # use default voltage from first appliance if present, otherwise 230
        voltage = services.to_decimal(appliances.first().voltage or Decimal('230'))
        try:
            total_current = services.power_to_current(total_power, voltage)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        adjusted = services.adjusted_current_for_safety(total_current)
        recommendations = services.recommend_wires_for_current(total_current)
        breaker = services.recommend_breaker_for_current(total_current)

        out = {
            'total_power_watts': total_power,
            'total_current': total_current,
            'adjusted_current': adjusted,
            'recommended_breaker': breaker,
            'recommendations': recommendations,
        }
        return Response(out)
