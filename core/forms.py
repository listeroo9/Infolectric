"""
Forms for the Infolectric application.
Includes forms for Component, Category, and WireSize models.
"""

from django import forms
from .models import Component, Category, WireSize
from .models import ApplianceLoad


class CategoryForm(forms.ModelForm):
    """
    Form for creating and editing electrical component categories.
    """
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category description',
                'rows': 3
            })
        }


class ComponentForm(forms.ModelForm):
    """
    Form for creating and editing electrical components.
    Includes validation for component details.
    """
    class Meta:
        model = Component
        fields = ['name', 'description', 'category', 'image']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter component name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter detailed component description',
                'rows': 5
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }

    def clean_name(self):
        """Validate that component name is not empty."""
        name = self.cleaned_data.get('name')
        if name and len(name.strip()) == 0:
            raise forms.ValidationError('Component name cannot be empty.')
        return name

    def clean_description(self):
        """Validate that description is not empty."""
        description = self.cleaned_data.get('description')
        if description and len(description.strip()) == 0:
            raise forms.ValidationError('Component description cannot be empty.')
        return description


class WireSizeForm(forms.ModelForm):
    """
    Form for creating and editing wire size specifications.
    Includes validation for electrical values.
    """
    class Meta:
        model = WireSize
        fields = ['wire_size_mm2', 'max_ampacity', 'description']
        widgets = {
            'wire_size_mm2': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter wire size in mm²',
                'step': '0.01'
            }),
            'max_ampacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter maximum ampacity in amps',
                'min': '1'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter wire application and description',
                'rows': 3
            })
        }

    def clean_max_ampacity(self):
        """Validate ampacity is a positive integer."""
        ampacity = self.cleaned_data.get('max_ampacity')
        if ampacity and ampacity <= 0:
            raise forms.ValidationError('Ampacity must be greater than 0.')
        return ampacity


class WireCalculatorForm(forms.Form):
    """
    Form for the wire recommendation calculator.
    Supports power + voltage calculation or direct current input.
    """
    power_watts = forms.DecimalField(
        label='Power (Watts)',
        required=False,
        min_value=0.01,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter power in watts',
            'step': '0.1'
        })
    )
    voltage = forms.DecimalField(
        label='Voltage (Volts)',
        required=False,
        min_value=0.1,
        decimal_places=2,
        initial=220,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter voltage in volts',
            'step': '0.1'
        })
    )
    current = forms.DecimalField(
        label='Current (Amps)',
        required=False,
        min_value=0.01,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter current in amperes (optional)',
            'step': '0.1'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        power = cleaned_data.get('power_watts')
        voltage = cleaned_data.get('voltage')
        current = cleaned_data.get('current')

        if current is None and power is None:
            raise forms.ValidationError(
                'Provide either current directly or both power and voltage.'
            )

        if current is None:
            if voltage is None:
                cleaned_data['voltage'] = Decimal('220.00')
                voltage = cleaned_data['voltage']
            try:
                cleaned_data['calculated_current'] = Decimal(power) / Decimal(voltage)
            except Exception:
                raise forms.ValidationError('Power and voltage must be valid numbers.')
        else:
            cleaned_data['calculated_current'] = current

        return cleaned_data


class ApplianceLoadForm(forms.ModelForm):
    class Meta:
        model = ApplianceLoad
        fields = ['name', 'voltage', 'power_watts', 'category']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'voltage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'power_watts': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }


class ProjectBuilderForm(forms.Form):
    """Form to select multiple appliances to build a project load."""
    appliances = forms.ModelMultipleChoiceField(
        queryset=ApplianceLoad.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 8}),
        required=True
    )
