"""
Views for the Infolectric application.
Includes CRUD views, search, filtering, and calculator functionality.
"""

from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib import messages
from .models import Component, Category, WireSize
from .forms import ComponentForm, CategoryForm, WireSizeForm, WireCalculatorForm, WireExplorerForm
from .models import ApplianceLoad
from .forms import ApplianceLoadForm, ProjectBuilderForm
from . import services


# ============================================================================
# CATEGORY VIEWS
# ============================================================================

class CategoryListView(ListView):
    """Display list of all electrical component categories."""
    model = Category
    template_name = 'core/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20


class CategoryDetailView(DetailView):
    """Display detailed view of a category with its components."""
    model = Category
    template_name = 'core/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all components in this category
        context['components'] = self.object.components.all()
        return context


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """Create a new electrical component category."""
    model = Category
    form_class = CategoryForm
    template_name = 'core/category_form.html'
    success_url = reverse_lazy('core:category-list')

    def form_valid(self, form):
        messages.success(self.request, f"Category '{form.cleaned_data['name']}' created successfully!")
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing electrical component category."""
    model = Category
    form_class = CategoryForm
    template_name = 'core/category_form.html'
    success_url = reverse_lazy('core:category-list')

    def form_valid(self, form):
        messages.success(self.request, f"Category '{form.cleaned_data['name']}' updated successfully!")
        return super().form_valid(form)


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an electrical component category."""
    model = Category
    template_name = 'core/category_confirm_delete.html'
    success_url = reverse_lazy('core:category-list')

    def delete(self, request, *args, **kwargs):
        category_name = self.get_object().name
        messages.success(request, f"Category '{category_name}' deleted successfully!")
        return super().delete(request, *args, **kwargs)


# ============================================================================
# COMPONENT VIEWS
# ============================================================================

class ComponentListView(ListView):
    """Display list of all electrical components with search and filtering."""
    model = Component
    template_name = 'core/component_list.html'
    context_object_name = 'components'
    paginate_by = 12

    def get_queryset(self):
        """Filter components by search query and category."""
        queryset = Component.objects.all()
        
        # Search by component name
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        # Filter by category
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add categories to context for filtering dropdown
        context['categories'] = Category.objects.all()
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_category'] = self.request.GET.get('category', '')
        return context


class ComponentDetailView(DetailView):
    """Display detailed view of a single electrical component."""
    model = Component
    template_name = 'core/component_detail.html'
    context_object_name = 'component'


class ComponentCreateView(LoginRequiredMixin, CreateView):
    """Create a new electrical component."""
    model = Component
    form_class = ComponentForm
    template_name = 'core/component_form.html'
    success_url = reverse_lazy('core:component-list')

    def form_valid(self, form):
        messages.success(self.request, f"Component '{form.cleaned_data['name']}' created successfully!")
        return super().form_valid(form)


class ComponentUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing electrical component."""
    model = Component
    form_class = ComponentForm
    template_name = 'core/component_form.html'

    def get_success_url(self):
        return reverse_lazy('core:component-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f"Component '{form.cleaned_data['name']}' updated successfully!")
        return super().form_valid(form)


class ComponentDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an electrical component."""
    model = Component
    template_name = 'core/component_confirm_delete.html'
    success_url = reverse_lazy('core:component-list')

    def delete(self, request, *args, **kwargs):
        component_name = self.get_object().name
        messages.success(request, f"Component '{component_name}' deleted successfully!")
        return super().delete(request, *args, **kwargs)


# ============================================================================
# WIRE SIZE VIEWS
# ============================================================================

class WireSizeListView(ListView):
    """Display list of all wire size specifications."""
    model = WireSize
    template_name = 'core/wiresize_list.html'
    context_object_name = 'wire_sizes'
    paginate_by = 20


class WireSizeDetailView(DetailView):
    """Display detailed view of a wire size specification."""
    model = WireSize
    template_name = 'core/wiresize_detail.html'
    context_object_name = 'wire_size'


class WireSizeCreateView(LoginRequiredMixin, CreateView):
    """Create a new wire size specification."""
    model = WireSize
    form_class = WireSizeForm
    template_name = 'core/wiresize_form.html'
    success_url = reverse_lazy('core:wiresize-list')

    def form_valid(self, form):
        messages.success(
            self.request,
            f"Wire size {form.cleaned_data['wire_size_mm2']}mm² created successfully!"
        )
        return super().form_valid(form)


class WireSizeUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing wire size specification."""
    model = WireSize
    form_class = WireSizeForm
    template_name = 'core/wiresize_form.html'

    def get_success_url(self):
        return reverse_lazy('core:wiresize-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(
            self.request,
            f"Wire size {form.cleaned_data['wire_size_mm2']}mm² updated successfully!"
        )
        return super().form_valid(form)


class WireSizeDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a wire size specification."""
    model = WireSize
    template_name = 'core/wiresize_confirm_delete.html'
    success_url = reverse_lazy('core:wiresize-list')

    def delete(self, request, *args, **kwargs):
        wire_size = self.get_object().wire_size_mm2
        messages.success(request, f"Wire size {wire_size}mm² deleted successfully!")
        return super().delete(request, *args, **kwargs)


# ============================================================================
# GENERAL VIEWS
# ============================================================================

def index(request):
    """Homepage view with overview of the platform."""
    context = {
        'component_count': Component.objects.count(),
        'category_count': Category.objects.count(),
        'wiresize_count': WireSize.objects.count(),
        'recent_components': Component.objects.all()[:5],
    }
    return render(request, 'core/index.html', context)


# ============================================================================
# WIRE CALCULATOR VIEW
# ============================================================================

def wire_calculator(request):
    """
    Wire size recommendation calculator.
    Supports power + voltage or direct current input, plus wire explorer mode.
    """
    from django.db.models import Max

    form = WireCalculatorForm()
    explorer_form = WireExplorerForm()
    recommendations = None
    error_message = None
    result = None
    used_current_mode = False
    explorer_results = None
    active_tab = request.POST.get('active_tab') or request.GET.get('tab', 'recommendation')

    if request.method == 'POST':
        active_tab = request.POST.get('active_tab', 'recommendation')
        if active_tab == 'explorer':
            explorer_form = WireExplorerForm(request.POST)
            if explorer_form.is_valid():
                wire_size = explorer_form.cleaned_data['wire_size']
                try:
                    capability = services.get_wire_capability(wire_size=wire_size)
                    compatible_appliances = services.get_compatible_appliances(wire_size)
                    safe_combinations = services.generate_safe_combinations(wire_size)
                    explorer_results = {
                        'capability': capability,
                        'compatible_appliances': compatible_appliances,
                        'safe_combinations': safe_combinations,
                        'compatible_count': len(compatible_appliances),
                    }
                except Exception as exc:
                    error_message = str(exc)
        else:
            form = WireCalculatorForm(request.POST)
            if form.is_valid():
                power = form.cleaned_data.get('power_watts')
                voltage = form.cleaned_data.get('voltage')
                current = form.cleaned_data.get('current')

                try:
                    current_value = services.calculate_current(
                        power_watts=power,
                        voltage=voltage,
                        current=current
                    )
                    adjusted_current = services.adjusted_current_for_safety(current_value)
                    recommendations = services.recommend_wires_for_current(current_value)
                    used_current_mode = current is not None and power is None

                    if not recommendations:
                        max_available = WireSize.objects.aggregate(max_amp=Max('max_ampacity'))['max_amp']
                        error_message = (
                            f"No wire sizes found for adjusted current {adjusted_current}A. "
                            f"Maximum available ampacity is {max_available}A."
                        )
                    else:
                        result = {
                            'power_watts': power,
                            'voltage': voltage or Decimal('220'),
                            'current': current_value,
                            'adjusted_current': adjusted_current,
                        }
                except Exception as exc:
                    error_message = str(exc)

    context = {
        'form': form,
        'explorer_form': explorer_form,
        'recommendations': recommendations,
        'error_message': error_message,
        'result': result,
        'used_current_mode': used_current_mode,
        'explorer_results': explorer_results,
        'active_tab': active_tab,
        'wire_sizes': WireSize.objects.all().order_by('wire_size_mm2'),
    }
    return render(request, 'core/wire_calculator.html', context)


def power_calculator_view(request):
    """Power -> current calculator page which also recommends wire sizes."""
    form = None
    result = None
    error = None
    recommendations = None

    if request.method == 'POST':
        from .forms import WireCalculatorForm
        # reuse WireCalculatorForm fields but expect both power and voltage
        power = request.POST.get('power_watts')
        voltage = request.POST.get('voltage')
        try:
            if not power or not voltage:
                raise ValueError('Power and voltage are required')
            current = services.power_to_current(power, voltage)
            adjusted = services.adjusted_current_for_safety(current)
            recommendations = services.recommend_wires_for_current(current)
            result = {
                'power_watts': power,
                'voltage': voltage,
                'current': current,
                'adjusted_current': adjusted,
            }
        except Exception as exc:
            error = str(exc)

    # simple form context (we don't need a formal Django form here)
    appliances = ApplianceLoad.objects.all()
    context = {
        'form': form,
        'result': result,
        'error': error,
        'recommendations': recommendations,
        'appliances': appliances,
    }
    return render(request, 'core/power_calculator.html', context)


class ApplianceListView(ListView):
    model = ApplianceLoad
    template_name = 'core/appliance_list.html'
    context_object_name = 'appliances'
    paginate_by = 20


class ApplianceDetailView(DetailView):
    model = ApplianceLoad
    template_name = 'core/appliance_detail.html'
    context_object_name = 'appliance'


class ApplianceCreateView(LoginRequiredMixin, CreateView):
    model = ApplianceLoad
    form_class = ApplianceLoadForm
    template_name = 'core/appliance_form.html'
    success_url = reverse_lazy('core:appliance-list')

    def form_valid(self, form):
        messages.success(self.request, f"Appliance '{form.cleaned_data['name']}' created successfully!")
        return super().form_valid(form)


class ApplianceUpdateView(LoginRequiredMixin, UpdateView):
    model = ApplianceLoad
    form_class = ApplianceLoadForm
    template_name = 'core/appliance_form.html'

    def get_success_url(self):
        return reverse_lazy('core:appliance-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f"Appliance '{form.cleaned_data['name']}' updated successfully!")
        return super().form_valid(form)


class ApplianceDeleteView(LoginRequiredMixin, DeleteView):
    model = ApplianceLoad
    template_name = 'core/appliance_confirm_delete.html'
    success_url = reverse_lazy('core:appliance-list')

    def delete(self, request, *args, **kwargs):
        name = self.get_object().name
        messages.success(request, f"Appliance '{name}' deleted successfully!")
        return super().delete(request, *args, **kwargs)


def ProjectBuilderView(request):
    """Select multiple appliances to summarise and get recommendations."""
    form = ProjectBuilderForm(request.POST or None)
    output = None
    error = None
    if request.method == 'POST' and form.is_valid():
        appliances = form.cleaned_data['appliances']
        total_power = sum([float(a.power_watts or 0) for a in appliances])
        voltage = float(appliances.first().voltage or 230)
        try:
            total_current = services.power_to_current(total_power, voltage)
        except ValueError as exc:
            error = str(exc)
            total_current = None

        if total_current is not None:
            adjusted = services.adjusted_current_for_safety(total_current)
            recommendations = services.recommend_wires_for_current(total_current)
            breaker = services.recommend_breaker_for_current(total_current)
            output = {
                'total_power_watts': total_power,
                'total_current': total_current,
                'adjusted_current': adjusted,
                'recommended_breaker': breaker,
                'recommendations': recommendations,
            }

    context = {
        'form': form,
        'output': output,
        'error': error,
    }
    return render(request, 'core/project_builder.html', context)
