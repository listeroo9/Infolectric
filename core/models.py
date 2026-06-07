"""
Models for the Infolectric application.
Includes Component, Category, and WireSize models.
"""

from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.db import models
from django.db.models import Count
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.html import format_html
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save

try:
    # allauth SocialAccount may or may not be installed in some environments
    from allauth.socialaccount.models import SocialAccount
except Exception:
    SocialAccount = None


class Category(models.Model):
    """
    Represents a category for electrical components.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    @classmethod
    def with_components(cls):
        return cls.objects.annotate(component_count=Count('components')).filter(component_count__gt=0)

    def __str__(self):
        return self.name


class Component(models.Model):
    """
    Represents an electrical component with detailed information.
    """
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='components')
    image = models.ImageField(
        upload_to='component_images/',
        blank=True,
        null=True,
        help_text='Upload an image of the component'
    )
    date_created = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_created']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.name


class WireSize(models.Model):
    """
    Represents wire size specifications with ampacity ratings.
    Used for wire recommendations based on current requirements.
    """
    wire_size_mm2 = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        unique=True,
        validators=[MinValueValidator(0.01)],
        verbose_name='Wire Size (mm²)'
    )
    max_ampacity = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text='Maximum safe current in amperes'
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text='Application and description'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['wire_size_mm2']
        verbose_name_plural = 'Wire Sizes'
        indexes = [
            models.Index(fields=['max_ampacity']),
        ]

    def __str__(self):
        return f"{self.wire_size_mm2}mm² ({self.max_ampacity}A)"


class ApplianceLoad(models.Model):
    """
    Represents an appliance or load with power and voltage specs.
    Estimated current is calculated on save (I = P / V).
    """
    name = models.CharField(max_length=200)
    voltage = models.DecimalField(max_digits=8, decimal_places=2, default=230)
    power_watts = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appliance_loads'
    )
    estimated_current = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        editable=False,
        help_text='Calculated as I = P / V'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.power_watts}W @ {self.voltage}V)"

    def save(self, *args, **kwargs):
        # Only compute estimated_current when stored fields are proper Decimals.
        # Avoid converting here; keep conversions centralized in services.
        if isinstance(self.power_watts, Decimal) and isinstance(self.voltage, Decimal) and self.voltage != 0:
            try:
                self.estimated_current = self.power_watts / self.voltage
            except Exception:
                self.estimated_current = None
        else:
            self.estimated_current = None

        super().save(*args, **kwargs)


class UserProfile(models.Model):
    """Stores optional user profile information and avatars."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    google_avatar_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.username}"


# Automatically create a UserProfile when a new User is created
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


# When a SocialAccount is saved (e.g., Google login), store the avatar URL
if SocialAccount is not None:
    @receiver(post_save, sender=SocialAccount)
    def update_profile_from_socialaccount(sender, instance, **kwargs):
        try:
            user = instance.user
            extra = instance.extra_data or {}
            # Common key for Google profile picture
            avatar = extra.get('picture') or extra.get('avatar_url') or extra.get('picture_url')
            if avatar:
                profile, _ = UserProfile.objects.get_or_create(user=user)
                if profile.google_avatar_url != avatar:
                    profile.google_avatar_url = avatar
                    profile.save()
        except Exception:
            # Avoid breaking auth flow on unexpected data
            pass


class ChangeRequest(models.Model):
    """Tracks user contribution requests and admin approval workflow."""

    TARGET_MODEL_CATEGORY = 'category'
    TARGET_MODEL_COMPONENT = 'component'
    TARGET_MODEL_APPLIANCE = 'appliance'
    TARGET_MODEL_WIRESIZE = 'wiresize'
    TARGET_MODEL_CHOICES = [
        (TARGET_MODEL_CATEGORY, 'Category'),
        (TARGET_MODEL_COMPONENT, 'Component'),
        (TARGET_MODEL_APPLIANCE, 'Appliance'),
        (TARGET_MODEL_WIRESIZE, 'Wire Size'),
    ]

    REQUEST_TYPE_ADD = 'add'
    REQUEST_TYPE_EDIT = 'edit'
    REQUEST_TYPE_DELETE = 'delete'
    REQUEST_TYPE_CHOICES = [
        (REQUEST_TYPE_ADD, 'Add Request'),
        (REQUEST_TYPE_EDIT, 'Edit Request'),
        (REQUEST_TYPE_DELETE, 'Delete Request'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    request_type = models.CharField(max_length=10, choices=REQUEST_TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='change_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    target_model = models.CharField(max_length=20, choices=TARGET_MODEL_CHOICES)
    target_object_id = models.PositiveIntegerField(null=True, blank=True)

    title = models.CharField(max_length=255)
    description = models.TextField()
    reason = models.TextField(blank=True)
    payload = models.JSONField(blank=True, null=True)

    admin_notes = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_requests'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='rejected_requests'
    )
    rejected_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_request_type_display()} - {self.title} ({self.get_status_display()})"

    def get_target_model_class(self):
        mapping = {
            self.TARGET_MODEL_CATEGORY: Category,
            self.TARGET_MODEL_COMPONENT: Component,
            self.TARGET_MODEL_APPLIANCE: ApplianceLoad,
            self.TARGET_MODEL_WIRESIZE: WireSize,
        }
        return mapping.get(self.target_model)

    def get_target_object(self):
        model_class = self.get_target_model_class()
        if model_class and self.target_object_id:
            return model_class.objects.filter(pk=self.target_object_id).first()
        return None

    def is_pending(self):
        return self.status == self.STATUS_PENDING

    def cancel(self):
        if not self.is_pending():
            raise ValueError('Only pending requests can be cancelled.')
        self.status = self.STATUS_CANCELLED
        self.cancelled_at = timezone.now()
        self.save()

    def _validate_payload(self):
        if self.request_type in {self.REQUEST_TYPE_ADD, self.REQUEST_TYPE_EDIT} and not self.payload:
            raise ValueError('Payload is required for add and edit requests.')

    def _create_target(self):
        model_class = self.get_target_model_class()
        if not model_class:
            raise ValueError('Unsupported target model for add request.')
        self._validate_payload()

        create_kwargs = {}
        for key, value in self.payload.items():
            if key == 'new_category_name':
                continue
            if (
                model_class is Component and
                key == 'category' and
                value == 'new'
            ):
                new_category_name = str(self.payload.get('new_category_name', '')).strip()
                if not new_category_name:
                    raise ValueError('New category name is required for new category requests.')
                category_obj = Category.objects.filter(name__iexact=new_category_name).first()
                if not category_obj:
                    category_obj = Category.objects.create(name=new_category_name)
                create_kwargs['category_id'] = category_obj.pk
                continue

            try:
                field = model_class._meta.get_field(key)
            except Exception:
                create_kwargs[key] = value
            else:
                if isinstance(field, models.FileField) or isinstance(field, models.ImageField):
                    if isinstance(value, dict):
                        value = value.get('path') or value.get('name')
                    create_kwargs[key] = value
                elif isinstance(field, models.ForeignKey):
                    create_kwargs[f'{key}_id'] = value
                else:
                    create_kwargs[key] = value

        instance = model_class(**create_kwargs)
        instance.save()
        self.target_object_id = instance.pk
        return instance

    def _update_target(self):
        self._validate_payload()
        target = self.get_target_object()
        if not target:
            raise ValueError('Target object not found for edit request.')

        for key, value in self.payload.items():
            if key == 'new_category_name':
                continue
            if (
                isinstance(target, Component) and
                key == 'category' and
                value == 'new'
            ):
                new_category_name = str(self.payload.get('new_category_name', '')).strip()
                if not new_category_name:
                    raise ValueError('New category name is required for new category requests.')
                category_obj = Category.objects.filter(name__iexact=new_category_name).first()
                if not category_obj:
                    category_obj = Category.objects.create(name=new_category_name)
                setattr(target, 'category_id', category_obj.pk)
                continue

            try:
                field = target._meta.get_field(key)
            except Exception:
                setattr(target, key, value)
            else:
                if isinstance(field, models.FileField) or isinstance(field, models.ImageField):
                    if isinstance(value, dict):
                        value = value.get('path') or value.get('name')
                    setattr(target, key, value)
                elif isinstance(field, models.ForeignKey):
                    setattr(target, f'{key}_id', value)
                else:
                    setattr(target, key, value)

        target.save()
        return target

    def _delete_target(self):
        target = self.get_target_object()
        if not target:
            raise ValueError('Target object not found for delete request.')
        target.delete()
        return None

    def _display_value_for_field(self, model_class, field_name, value):
        """Return a human-friendly display value for a field value (resolves FKs)."""
        if (
            self.target_model == self.TARGET_MODEL_COMPONENT and
            field_name == 'category' and
            value == 'new'
        ):
            return self.payload.get('new_category_name') or 'Requested New Category'

        if model_class is None:
            return value
        try:
            field = model_class._meta.get_field(field_name)
        except Exception:
            return value
        # ForeignKey -> resolve instance by pk
        if isinstance(field, models.ForeignKey):
            rel_model = field.remote_field.model
            try:
                obj = rel_model.objects.filter(pk=value).first()
                return str(obj) if obj is not None else value
            except Exception:
                return value
        # File/Image fields -> render a thumbnail or link when possible.
        if isinstance(field, (models.FileField, models.ImageField)) and value:
            try:
                # payload may store {'path': 'relative/path.jpg'} or {'name': 'file.jpg'} or a plain path
                if isinstance(value, dict):
                    file_path = value.get('path') or value.get('name')
                elif hasattr(value, 'name'):
                    file_path = value.name
                else:
                    file_path = str(value)

                # Build URL using MEDIA_URL
                media_url = getattr(settings, 'MEDIA_URL', '/media/')
                url = f"{media_url}{file_path}".replace('\\', '/')
                return format_html('<img src="{}" class="img-fluid img-thumbnail" style="max-width:200px;">', url)
            except Exception:
                return value
        return value

    def get_change_summary(self):
        """Return a list of (label, old, new) tuples describing the requested change.

        - For add requests: old will be None, new holds proposed values.
        - For edit requests: old and new show previous and proposed values.
        - For delete requests: single entry with the object representation.
        """
        model_class = self.get_target_model_class()
        payload = self.payload or {}
        summary = []

        if self.request_type == self.REQUEST_TYPE_ADD:
            for key, new_val in payload.items():
                if model_class is not None:
                    try:
                        field = model_class._meta.get_field(key)
                        label = getattr(field, 'verbose_name', key).title()
                    except Exception:
                        label = key.replace('_', ' ').title()
                else:
                    label = key.replace('_', ' ').title()
                new_display = self._display_value_for_field(model_class, key, new_val)
                summary.append((label, None, new_display))

        elif self.request_type == self.REQUEST_TYPE_EDIT:
            target = self.get_target_object()
            for key, new_val in payload.items():
                if target is not None:
                    try:
                        field = target._meta.get_field(key)
                        label = getattr(field, 'verbose_name', key).title()
                    except Exception:
                        label = key.replace('_', ' ').title()
                else:
                    label = key.replace('_', ' ').title()
                old_raw = getattr(target, key, None) if target is not None else None
                old_display = self._display_value_for_field(model_class, key, old_raw) if target is not None else None
                new_display = self._display_value_for_field(model_class, key, new_val)
                summary.append((label, old_display, new_display))

        elif self.request_type == self.REQUEST_TYPE_DELETE:
            target = self.get_target_object()
            summary.append((('Object'), str(target) if target is not None else f"ID {self.target_object_id}", None))

        return summary

    def approve(self, user, notes=''):
        if not self.is_pending():
            raise ValueError('Only pending requests can be approved.')
        if not user.is_staff and not user.is_superuser:
            raise PermissionError('Only staff can approve requests.')

        if self.request_type == self.REQUEST_TYPE_ADD:
            self._create_target()
        elif self.request_type == self.REQUEST_TYPE_EDIT:
            self._update_target()
        elif self.request_type == self.REQUEST_TYPE_DELETE:
            self._delete_target()
        else:
            raise ValueError('Unsupported request type.')

        self.status = self.STATUS_APPROVED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.admin_notes = notes or self.admin_notes
        self.save()
        return self

    def reject(self, user, notes=''):
        if not self.is_pending():
            raise ValueError('Only pending requests can be rejected.')
        if not user.is_staff and not user.is_superuser:
            raise PermissionError('Only staff can reject requests.')

        self.status = self.STATUS_REJECTED
        self.rejected_by = user
        self.rejected_at = timezone.now()
        self.admin_notes = notes or self.admin_notes
        self.save()
        return self
