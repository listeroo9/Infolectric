"""
URL routing for the core app.
Includes both regular views and API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

app_name = 'core'

# ============================================================================
# REST Framework API Router
# ============================================================================
router = DefaultRouter()
router.register(r'categories', api_views.CategoryViewSet, basename='api-category')
router.register(r'components', api_views.ComponentViewSet, basename='api-component')
router.register(r'wire-sizes', api_views.WireSizeViewSet, basename='api-wiresize')
router.register(r'wire-recommendation', api_views.WireRecommendationViewSet, basename='api-wire-recommendation')

urlpatterns = [
    # ========================================================================
    # API ROUTES
    # ========================================================================
    path('api/', include(router.urls)),

    # ========================================================================
    # HOME
    # ========================================================================
    path('', views.index, name='index'),

    # ========================================================================
    # CATEGORY ROUTES
    # ========================================================================
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category-create'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),
    path('categories/<int:pk>/update/', views.CategoryUpdateView.as_view(), name='category-update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category-delete'),

    # ========================================================================
    # COMPONENT ROUTES
    # ========================================================================
    path('components/', views.ComponentListView.as_view(), name='component-list'),
    path('components/create/', views.ComponentCreateView.as_view(), name='component-create'),
    path('components/<int:pk>/', views.ComponentDetailView.as_view(), name='component-detail'),
    path('components/<int:pk>/update/', views.ComponentUpdateView.as_view(), name='component-update'),
    path('components/<int:pk>/delete/', views.ComponentDeleteView.as_view(), name='component-delete'),

    # ========================================================================
    # WIRE SIZE ROUTES
    # ========================================================================
    path('wire-sizes/', views.WireSizeListView.as_view(), name='wiresize-list'),
    path('wire-sizes/create/', views.WireSizeCreateView.as_view(), name='wiresize-create'),
    path('wire-sizes/<int:pk>/', views.WireSizeDetailView.as_view(), name='wiresize-detail'),
    path('wire-sizes/<int:pk>/update/', views.WireSizeUpdateView.as_view(), name='wiresize-update'),
    path('wire-sizes/<int:pk>/delete/', views.WireSizeDeleteView.as_view(), name='wiresize-delete'),

    # ========================================================================
    # CALCULATOR ROUTES
    # ========================================================================
    path('calculator/', views.wire_calculator, name='calculator'),
]
