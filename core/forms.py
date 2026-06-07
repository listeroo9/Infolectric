"""
Forms for the Infolectric application.
Includes forms for Component, Category, and WireSize models.
"""

from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from .models import Component, Category, WireSize, ChangeRequest
from .models import ApplianceLoad
from . import services
from django.core.files.uploadedfile import InMemoryUploadedFile


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


class ComponentCategoryChoiceField(forms.ModelChoiceField):
    def to_python(self, value):
        if value == 'new':
            return 'new'
        return super().to_python(value)

    def validate(self, value):
        if value == 'new':
            return
        super().validate(value)

    def clean(self, value):
        """Override clean to allow the 'new' sentinel value to bypass queryset validation."""
        if value == 'new':
            return 'new'
        return super().clean(value)


class ComponentForm(forms.ModelForm):
    """
    Form for creating and editing electrical components.
    Includes validation for component details.
    """
    category = ComponentCategoryChoiceField(
        queryset=Category.objects.all().order_by('name'),
        empty_label='Select a category',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    new_category_name = forms.CharField(
        required=False,
        label='New Category Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new category name'
        })
    )

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
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if self.instance and self.instance.pk and self.instance.category:
            self.fields['category'].initial = self.instance.category

        choices = list(self.fields['category'].choices)
        if choices and choices[-1][0] != 'new':
            choices.append(('new', '➕ Add New Category'))
            self.fields['category'].choices = choices

    def clean_new_category_name(self):
        new_category_name = self.cleaned_data.get('new_category_name', '')
        raw_category = self.data.get('category')

        if raw_category == 'new':
            trimmed_name = new_category_name.strip()
            if not trimmed_name:
                raise forms.ValidationError('New category name is required when adding a new category.')
            return trimmed_name

        return ''

    def clean(self):
        cleaned = super().clean()
        raw_category = self.data.get('category', '').strip()
        new_category_name = cleaned.get('new_category_name', '').strip()

        # If 'new' is selected, require new_category_name
        if raw_category == 'new':
            if not new_category_name:
                raise forms.ValidationError(
                    {'category': 'New category name is required when selecting "Add New Category".'}
                )
            cleaned['category'] = None
            cleaned['new_category_name'] = new_category_name
        else:
            # If not 'new', ensure a category is selected
            category_obj = cleaned.get('category')
            if not category_obj:
                raise forms.ValidationError(
                    {'category': 'Please select a category or add a new one.'}
                )
            cleaned['new_category_name'] = ''

        return cleaned

    def save(self, commit=True):
        category_obj = self.cleaned_data.get('category')
        new_category_name = self.cleaned_data.get('new_category_name', '').strip()

        if not category_obj and new_category_name:
            normalized_name = new_category_name.strip()
            category_obj = Category.objects.filter(name__iexact=normalized_name).first()
            if not category_obj:
                category_obj = Category.objects.create(name=normalized_name)

        if not category_obj:
            raise forms.ValidationError(
                'Category could not be resolved. Please select an existing category or provide a new category name.'
            )

        self.instance.category = category_obj
        return super().save(commit=commit)

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
        min_value=Decimal('0.01'),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter power in watts',
            'step': 'any'
        })
    )
    voltage = forms.DecimalField(
        label='Voltage (Volts)',
        required=False,
        min_value=Decimal('0.1'),
        max_digits=8,
        decimal_places=2,
        initial=Decimal('220.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter voltage in volts',
            'step': 'any'
        })
    )
    current = forms.DecimalField(
        label='Current (Amps)',
        required=False,
        min_value=Decimal('0.01'),
        max_digits=10,
        decimal_places=4,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter current in amperes (optional)',
            'step': 'any'
        })
    )
    wire_length = forms.DecimalField(
        label='Wire Length (meters)',
        required=False,
        min_value=Decimal('0.01'),
        initial=Decimal('10.00'),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter wire length in meters',
            'step': 'any'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        power = cleaned_data.get('power_watts')
        voltage = cleaned_data.get('voltage')
        current = cleaned_data.get('current')
        wire_length = cleaned_data.get('wire_length')

        if current is None and power is None:
            raise forms.ValidationError(
                'Provide either current directly or both power and voltage.'
            )

        if wire_length is None:
            cleaned_data['wire_length'] = Decimal('10.00')

        if current is None:
            if voltage is None:
                cleaned_data['voltage'] = Decimal('220.00')
                voltage = cleaned_data['voltage']
            try:
                cleaned_data['calculated_current'] = Decimal(str(power)) / Decimal(str(voltage))
            except Exception:
                raise forms.ValidationError('Power and voltage must be valid numbers.')
        else:
            cleaned_data['calculated_current'] = Decimal(str(current))

        return cleaned_data


class WireExplorerForm(forms.Form):
    """Form for selecting a wire size to explore its capability."""
    wire_size = forms.ModelChoiceField(
        queryset=WireSize.objects.all().order_by('wire_size_mm2'),
        label='Wire Size',
        empty_label='Select a wire size',
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    usage_type = forms.ChoiceField(
        label='Usage Type',
        choices=services.USAGE_TYPE_CHOICES,
        initial=services.USAGE_TYPE_NORMAL_HOUSEHOLD,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    wire_length = forms.DecimalField(
        label='Wire Length (meters)',
        required=False,
        min_value=Decimal('0.01'),
        initial=Decimal('10.00'),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter wire length in meters',
            'step': 'any'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('wire_length') is None:
            cleaned_data['wire_length'] = Decimal('10.00')
        if not cleaned_data.get('usage_type'):
            cleaned_data['usage_type'] = services.USAGE_TYPE_NORMAL_HOUSEHOLD
        return cleaned_data


class ApplianceLoadForm(forms.ModelForm):
    class Meta:
        model = ApplianceLoad
        fields = ['name', 'voltage', 'power_watts']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'voltage': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'power_watts': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
        }
    

class UserProfileForm(forms.Form):
    profile_image = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    remove_image = forms.BooleanField(required=False, initial=False, help_text='Remove uploaded image and revert to Google/default avatar')


class ChangeRequestForm(forms.ModelForm):
    target_object = forms.ModelChoiceField(
        queryset=Component.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = ChangeRequest
        fields = ['request_type', 'target_model', 'target_object', 'title', 'reason']
        widgets = {
            'request_type': forms.Select(attrs={'class': 'form-select'}),
            'target_model': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter request title'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Why is this change needed?', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        target_model = kwargs.pop('target_model', None)
        request_type = kwargs.pop('request_type', None)
        super().__init__(*args, **kwargs)
        if target_model:
            self.fields['target_model'].initial = target_model
            self.fields['target_object'].queryset = self.get_target_queryset(target_model)
        if request_type:
            self.fields['request_type'].initial = request_type
            self.fields['target_object'].required = request_type in {ChangeRequest.REQUEST_TYPE_EDIT, ChangeRequest.REQUEST_TYPE_DELETE}

    def get_target_queryset(self, target_model):
        if target_model == ChangeRequest.TARGET_MODEL_COMPONENT:
            return Component.objects.all()
        if target_model == ChangeRequest.TARGET_MODEL_APPLIANCE:
            return ApplianceLoad.objects.all()
        if target_model == ChangeRequest.TARGET_MODEL_WIRESIZE:
            return WireSize.objects.all()
        if target_model == ChangeRequest.TARGET_MODEL_CATEGORY:
            return Category.objects.all()
        return Component.objects.none()

    def save(self, commit=True):
        instance = super().save(commit=False)
        target_object = self.cleaned_data.get('target_object')
        instance.target_object_id = target_object.pk if target_object else None
        if commit:
            instance.save()
        return instance


class ChangeRequestReasonForm(forms.ModelForm):
    class Meta:
        model = ChangeRequest
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Explain why this change is needed.',
                'rows': 4
            }),
        }


class ComponentRequestPayloadForm(forms.ModelForm):
    class Meta:
        model = Component
        fields = ['name', 'description', 'category']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }


class ApplianceLoadRequestPayloadForm(forms.ModelForm):
    class Meta:
        model = ApplianceLoad
        fields = ['name', 'voltage', 'power_watts']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'voltage': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'power_watts': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
        }


class WireSizeRequestPayloadForm(forms.ModelForm):
    class Meta:
        model = WireSize
        fields = ['wire_size_mm2', 'max_ampacity', 'description']
        widgets = {
            'wire_size_mm2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_ampacity': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CategoryRequestPayloadForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class RequestAdminForm(forms.ModelForm):
    class Meta:
        model = ChangeRequest
        fields = ['title', 'reason', 'admin_notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'admin_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ProjectBuilderForm(forms.Form):
    """Form to select multiple appliances to build a project load."""
    appliances = forms.ModelMultipleChoiceField(
        queryset=ApplianceLoad.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 8}),
        required=True
    )


class InfolectricAuthenticationForm(AuthenticationForm):
    """Custom login form with optional remember-me support."""
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'name@example.com'
        })
    )
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class UserRegistrationForm(forms.Form):
    """Registration form for new Infolectric users."""
    username = forms.CharField(
        label='Username',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'})
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create a password'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        User = get_user_model()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        User = get_user_model()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')

        return cleaned_data

    def save(self):
        User = get_user_model()
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1']
        )
        return user
