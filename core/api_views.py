"""
API views for the Infolectric application.
RESTful API endpoints for components, categories, wire sizes, and calculator.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Component, Category, WireSize
from .serializers import (
    ComponentSerializer, CategorySerializer, WireSizeSerializer,
    WireRecommendationSerializer
)
from .serializers import ApplianceLoadSerializer, PowerToCurrentSerializer, ProjectBuilderOutputSerializer
from .models import ApplianceLoad
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
            "required_current": 10.5
        }
        
        Response:
        {
            "required_current": 10.5,
            "recommendations": [
                {
                    "id": 1,
                    "wire_size_mm2": "16.00",
                    "max_ampacity": 20,
                    "description": "Household circuits"
                }
            ]
        }
        """
        serializer = WireRecommendationSerializer(data=request.data)
        if serializer.is_valid():
            required_current = float(serializer.validated_data['required_current'])
            
            # Find all wire sizes with ampacity >= required current
            wire_sizes = WireSize.objects.filter(
                max_ampacity__gte=required_current
            ).order_by('wire_size_mm2')
            
            if not wire_sizes.exists():
                return Response(
                    {
                        'error': f'No wire sizes available for {required_current}A',
                        'required_current': required_current,
                        'recommendations': []
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            wire_serializer = WireSizeSerializer(wire_sizes, many=True)
            return Response({
                'required_current': required_current,
                'recommendations': wire_serializer.data
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
            power = serializer.validated_data['power_watts']
            voltage = serializer.validated_data['voltage']
            try:
                current = services.power_to_current(power, voltage)
            except ValueError as exc:
                return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

            recommendations = services.recommend_wires_for_current(current)
            out = {
                'power_watts': power,
                'voltage': voltage,
                'current': current,
                'recommendations': recommendations,
            }
            return Response(out)
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

        total_power = sum([float(a.power_watts or 0) for a in appliances])
        # use default voltage from first appliance if present, otherwise 230
        voltage = float(appliances.first().voltage or 230)
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
