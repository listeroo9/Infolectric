"""
Models for the Infolectric application.
Includes Component, Category, and WireSize models.
"""

from django.db import models
from django.core.validators import MinValueValidator


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
        # safe calculation: avoid division by zero
        try:
            v = float(self.voltage)
            p = float(self.power_watts)
            if v and v != 0:
                self.estimated_current = p / v
            else:
                self.estimated_current = None
        except Exception:
            self.estimated_current = None
        super().save(*args, **kwargs)
