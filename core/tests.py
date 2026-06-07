"""
Tests for the Infolectric application.
Run with: python manage.py test
"""

from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image
from core.models import ApplianceLoad, Component, Category, WireSize, ChangeRequest
from core import services


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


class UsageProfileServiceTest(TestCase):
    """Test usage profile calculations for wire exploration."""

    def test_calculate_usable_current_for_continuous_load(self):
        usable_current = services.calculate_usable_current(
            Decimal('6'),
            services.USAGE_TYPE_CONTINUOUS_LOAD
        )
        self.assertEqual(usable_current, Decimal('4.8'))

    def test_wire_capability_contains_usage_profile(self):
        wire_size = WireSize.objects.create(wire_size_mm2=1.5, max_ampacity=6)
        capability = services.get_wire_capability(
            wire_size=wire_size,
            usage_type=services.USAGE_TYPE_CONTINUOUS_LOAD
        )
        self.assertEqual(capability['usage_label'], 'Continuous Load')
        self.assertEqual(capability['usable_current'], Decimal('4.80'))
        self.assertEqual(capability['recommended_max_power'], Decimal('1056.00'))

    def test_generate_safe_combinations_returns_utilization_levels(self):
        wire_size = WireSize.objects.create(wire_size_mm2=2.5, max_ampacity=20)
        category = Category.objects.create(name='Household')
        ApplianceLoad.objects.create(name='LED Lamp', power_watts=20, voltage=220, category=category)
        ApplianceLoad.objects.create(name='Desk Fan', power_watts=50, voltage=220, category=category)
        ApplianceLoad.objects.create(name='Space Heater', power_watts=1200, voltage=220, category=category)

        combos = services.generate_safe_combinations(wire_size)
        self.assertEqual(len(combos), 5)
        self.assertTrue(all(combo['level'] in [1, 2, 3, 4, 5] for combo in combos))
        self.assertTrue(all(combo['total_current'] <= Decimal('18.00') for combo in combos))
        self.assertTrue(all('level_label' in combo for combo in combos))
        self.assertTrue(all('device_count' in combo for combo in combos))
        self.assertTrue(all('average_voltage' in combo for combo in combos))
        self.assertTrue(all('appliances' in combo for combo in combos))
        for combo in combos:
            self.assertTrue(all('current_amps' in appliance for appliance in combo['appliances']))
            self.assertTrue(all('contribution_percent' in appliance for appliance in combo['appliances']))
            self.assertEqual(combo['appliances'], sorted(combo['appliances'], key=lambda item: item['current_amps'], reverse=True))


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

    def test_component_list_excludes_empty_categories_in_filter_dropdown(self):
        """Empty categories should not appear in the component filter dropdown."""
        Category.objects.create(name='Capacitors')
        response = self.client.get(reverse('core:component-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resistors')
        self.assertNotContains(response, 'Capacitors')


class RequestWorkflowTest(TestCase):
    """Test change request submission and approval workflow."""

    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Resistors')
        self.user = User.objects.create_user(username='user', email='user@test.com', password='testpass123')
        self.admin = User.objects.create_superuser(username='admin', email='admin@test.com', password='testpass123')

    def test_user_can_submit_add_component_request(self):
        self.client.login(username='user', password='testpass123')
        response = self.client.post(reverse('core:component-create'), {
            'name': '1kΩ Resistor',
            'description': 'Standard 1kΩ resistor',
            'category': self.category.pk,
            'reason': 'Testing create request',
        })
        self.assertEqual(response.status_code, 302)
        # Component create by non-staff should create a ChangeRequest with title equal to the name
        self.assertTrue(ChangeRequest.objects.filter(title='1kΩ Resistor', user=self.user).exists())

    def test_admin_approves_request_creates_component(self):
        self.client.login(username='user', password='testpass123')
        response = self.client.post(reverse('core:component-create'), {
            'name': '2kΩ Resistor',
            'description': 'Standard 2kΩ resistor',
            'category': self.category.pk,
            'reason': 'Approve this component',
        })
        self.assertEqual(response.status_code, 302)
        request_obj = ChangeRequest.objects.get(title='2kΩ Resistor')
        self.client.logout()
        self.client.login(username='admin', password='testpass123')
        response = self.client.post(reverse('core:moderation-request-approve', kwargs={'pk': request_obj.pk}), {
            'admin_notes': 'Looks good',
        })
        self.assertEqual(response.status_code, 302)
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, ChangeRequest.STATUS_APPROVED)
        self.assertTrue(Component.objects.filter(name='2kΩ Resistor').exists())

    def test_approving_new_category_component_request_creates_category_and_component(self):
        self.client.login(username='user', password='testpass123')
        response = self.client.post(reverse('core:component-create'), {
            'name': '5kΩ Resistor',
            'description': 'Resistor in a new user-requested category',
            'category': 'new',
            'new_category_name': 'Capacitors',
            'reason': 'Request a new category with component',
        })
        self.assertEqual(response.status_code, 302)
        request_obj = ChangeRequest.objects.get(title='5kΩ Resistor')
        self.assertEqual(request_obj.payload.get('category'), 'new')
        self.assertEqual(request_obj.payload.get('new_category_name'), 'Capacitors')

        self.client.logout()
        self.client.login(username='admin', password='testpass123')
        response = self.client.post(reverse('core:moderation-request-approve', kwargs={'pk': request_obj.pk}), {
            'admin_notes': 'Approve new category request',
        })
        self.assertEqual(response.status_code, 302)
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, ChangeRequest.STATUS_APPROVED)
        component = Component.objects.get(name='5kΩ Resistor')
        self.assertEqual(component.category.name, 'Capacitors')

    def test_image_upload_request_stores_image_path_and_approves(self):
        self.client.login(username='user', password='testpass123')
        image_io = BytesIO()
        Image.new('RGB', (1, 1), color='white').save(image_io, format='PNG')
        image_io.seek(0)
        upload = SimpleUploadedFile(
            'resistor.png',
            image_io.read(),
            content_type='image/png'
        )
        response = self.client.post(reverse('core:component-create'), {
            'name': '3kΩ Resistor',
            'description': 'Resistor with image',
            'category': self.category.pk,
            'image': upload,
            'reason': 'Test image request',
        })
        self.assertEqual(response.status_code, 302)
        request_obj = ChangeRequest.objects.get(title='3kΩ Resistor')
        self.assertIn('path', request_obj.payload.get('image', {}))
        self.client.logout()
        self.client.login(username='admin', password='testpass123')
        response = self.client.post(reverse('core:moderation-request-approve', kwargs={'pk': request_obj.pk}), {
            'admin_notes': 'Approve image request',
        })
        self.assertEqual(response.status_code, 302)
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, ChangeRequest.STATUS_APPROVED)
        component = Component.objects.get(name='3kΩ Resistor')
        self.assertTrue(component.image.name)
        self.assertTrue(component.image.name.startswith('change_request_uploads/'))


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
