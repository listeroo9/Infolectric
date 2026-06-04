"""
Tests for the Infolectric application.
Run with: python manage.py test
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import Component, Category, WireSize


class CategoryModelTest(TestCase):
    """Test cases for Category model."""

    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(
            name="Resistors",
            description="Passive components that resist electric current flow"
        )

    def test_category_creation(self):
        """Test category can be created."""
        self.assertEqual(self.category.name, "Resistors")
        self.assertTrue(self.category.created_at)

    def test_category_str_representation(self):
        """Test category string representation."""
        self.assertEqual(str(self.category), "Resistors")


class ComponentModelTest(TestCase):
    """Test cases for Component model."""

    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(name="Resistors")
        self.component = Component.objects.create(
            name="10kΩ Resistor",
            description="Standard carbon film resistor",
            category=self.category
        )

    def test_component_creation(self):
        """Test component can be created."""
        self.assertEqual(self.component.name, "10kΩ Resistor")
        self.assertEqual(self.component.category, self.category)

    def test_component_str_representation(self):
        """Test component string representation."""
        self.assertEqual(str(self.component), "10kΩ Resistor")


class WireSizeModelTest(TestCase):
    """Test cases for WireSize model."""

    def setUp(self):
        """Set up test data."""
        self.wire_size = WireSize.objects.create(
            wire_size_mm2=2.5,
            max_ampacity=20,
            description="Standard for household outlet circuits"
        )

    def test_wire_size_creation(self):
        """Test wire size can be created."""
        self.assertEqual(self.wire_size.wire_size_mm2, 2.5)
        self.assertEqual(self.wire_size.max_ampacity, 20)

    def test_wire_size_str_representation(self):
        """Test wire size string representation."""
        expected = "2.50mm² (20A)"
        self.assertEqual(str(self.wire_size), expected)


class ComponentViewTest(TestCase):
    """Test cases for Component views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.category = Category.objects.create(name="Resistors")
        self.component = Component.objects.create(
            name="10kΩ Resistor",
            description="Standard carbon film resistor",
            category=self.category
        )
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )

    def test_component_list_view(self):
        """Test component list view."""
        response = self.client.get(reverse('core:component-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '10kΩ Resistor')
        self.assertTemplateUsed(response, 'core/component_list.html')

    def test_component_detail_view(self):
        """Test component detail view."""
        response = self.client.get(
            reverse('core:component-detail', kwargs={'pk': self.component.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '10kΩ Resistor')
        self.assertTemplateUsed(response, 'core/component_detail.html')

    def test_component_create_requires_login(self):
        """Test component creation requires login."""
        response = self.client.get(reverse('core:component-create'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_component_create_authenticated(self):
        """Test component creation for authenticated user."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('core:component-create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/component_form.html')

    def test_component_search(self):
        """Test component search functionality."""
        response = self.client.get(
            reverse('core:component-list'),
            {'q': 'resistor'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '10kΩ Resistor')

    def test_component_filter_by_category(self):
        """Test component filtering by category."""
        response = self.client.get(
            reverse('core:component-list'),
            {'category': self.category.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '10kΩ Resistor')


class CategoryViewTest(TestCase):
    """Test cases for Category views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.category = Category.objects.create(
            name="Resistors",
            description="Passive components"
        )
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )

    def test_category_list_view(self):
        """Test category list view."""
        response = self.client.get(reverse('core:category-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resistors')

    def test_category_detail_view(self):
        """Test category detail view."""
        response = self.client.get(
            reverse('core:category-detail', kwargs={'pk': self.category.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resistors')


class WireSizeViewTest(TestCase):
    """Test cases for WireSize views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.wire_size = WireSize.objects.create(
            wire_size_mm2=2.5,
            max_ampacity=20
        )

    def test_wiresize_list_view(self):
        """Test wire size list view."""
        response = self.client.get(reverse('core:wiresize-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '2.5')

    def test_wiresize_detail_view(self):
        """Test wire size detail view."""
        response = self.client.get(
            reverse('core:wiresize-detail', kwargs={'pk': self.wire_size.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '2.5')


class WireCalculatorViewTest(TestCase):
    """Test cases for wire calculator view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        WireSize.objects.create(wire_size_mm2=1.5, max_ampacity=15)
        WireSize.objects.create(wire_size_mm2=2.5, max_ampacity=20)
        WireSize.objects.create(wire_size_mm2=4.0, max_ampacity=32)

    def test_calculator_page_loads(self):
        """Test calculator page loads."""
        response = self.client.get(reverse('core:calculator'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/wire_calculator.html')

    def test_calculator_recommendation(self):
        """Test calculator provides recommendations."""
        response = self.client.post(
            reverse('core:calculator'),
            {'required_current': '10'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '2.5')  # 2.5mm² wire is recommended

    def test_calculator_no_wire_found(self):
        """Test calculator when no suitable wire is found."""
        response = self.client.post(
            reverse('core:calculator'),
            {'required_current': '999'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No wire sizes found')


class HomeViewTest(TestCase):
    """Test cases for home view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        Category.objects.create(name="Test Category")
        Component.objects.create(
            name="Test Component",
            description="Test",
            category=Category.objects.first()
        )
        WireSize.objects.create(wire_size_mm2=2.5, max_ampacity=20)

    def test_home_view(self):
        """Test home page view."""
        response = self.client.get(reverse('core:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/index.html')
        self.assertContains(response, 'Infolectric')

    def test_home_view_stats(self):
        """Test home page shows statistics."""
        response = self.client.get(reverse('core:index'))
        self.assertContains(response, '1')  # 1 component
