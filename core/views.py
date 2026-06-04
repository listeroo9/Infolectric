"""
Views for the Infolectric application.
Includes CRUD views, search, filtering, and calculator functionality.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib import messages
from .models import Component, Category, WireSize
from .forms import ComponentForm, CategoryForm, WireSizeForm, WireCalculatorForm


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
    User enters required current, system returns matching wire sizes.
    """
    from django.db.models import Max
    
    form = WireCalculatorForm()
    recommendations = None
    error_message = None
    required_current_value = None

    if request.method == 'POST':
        form = WireCalculatorForm(request.POST)
        if form.is_valid():
            required_current_value = float(form.cleaned_data['required_current'])
            
            # Find all wire sizes with ampacity >= required current
            recommendations = WireSize.objects.filter(
                max_ampacity__gte=required_current_value
            ).order_by('wire_size_mm2')
            
            if not recommendations:
                max_available = WireSize.objects.aggregate(max_amp=Max('max_ampacity'))['max_amp']
                error_message = (
                    f"No wire sizes found for {required_current_value}A. "
                    f"Maximum available ampacity is {max_available}A."
                )

    context = {
        'form': form,
        'recommendations': recommendations,
        'error_message': error_message,
        'required_current_value': required_current_value,
        'wire_sizes': WireSize.objects.all().order_by('wire_size_mm2'),
    }
    return render(request, 'core/wire_calculator.html', context)
