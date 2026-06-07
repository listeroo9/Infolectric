"""
Views for the Infolectric application.
Includes CRUD views, search, filtering, and calculator functionality.
"""

from decimal import Decimal
import os

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth import login as auth_login
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib import messages
from django.core.files.storage import default_storage
from django.utils.crypto import get_random_string
from .models import Component, Category, WireSize, ChangeRequest
from .models import ApplianceLoad, UserProfile
from .forms import (
    ComponentForm, CategoryForm, WireSizeForm,
    WireCalculatorForm, WireExplorerForm,
    ApplianceLoadForm, ProjectBuilderForm,
    ChangeRequestReasonForm, ComponentRequestPayloadForm,
    ApplianceLoadRequestPayloadForm, WireSizeRequestPayloadForm,
    CategoryRequestPayloadForm, RequestAdminForm,
    InfolectricAuthenticationForm, UserRegistrationForm
)
from .forms import UserProfileForm
from .models import ApplianceLoad
from . import services


class ManagementPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Require authenticated staff or superuser access for management actions."""
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_staff or user.is_superuser)


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
        # Admins create directly; authenticated non-staff submit a ChangeRequest
        user = self.request.user
        if user.is_staff or user.is_superuser:
            messages.success(self.request, f"Category '{form.cleaned_data['name']}' created successfully!")
            return super().form_valid(form)

        reason = normalize_request_reason(self.request)
        if not reason:
            form.add_error(None, 'Reason is required to submit a change request.')
            return self.form_invalid(form)

        payload = normalize_payload(form.cleaned_data)
        title = form.cleaned_data.get('name') or f"Create Category"
        cr = create_change_request(
            user=user,
            request_type=ChangeRequest.REQUEST_TYPE_ADD,
            target_model=ChangeRequest.TARGET_MODEL_CATEGORY,
            title=title,
            reason=reason,
            payload=payload,
        )
        cr.save()
        messages.success(self.request, 'Your request has been submitted for moderator approval.')
        return redirect('core:category-list')


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing electrical component category."""
    model = Category
    form_class = CategoryForm
    template_name = 'core/category_form.html'
    success_url = reverse_lazy('core:category-list')

    def form_valid(self, form):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            messages.success(self.request, f"Category '{form.cleaned_data['name']}' updated successfully!")
            return super().form_valid(form)

        reason = normalize_request_reason(self.request)
        if not reason:
            form.add_error(None, 'Reason is required to submit a change request.')
            return self.form_invalid(form)

        obj = self.get_object()
        payload = normalize_payload(form.cleaned_data)
        title = form.cleaned_data.get('name') or str(obj)
        cr = create_change_request(
            user=user,
            request_type=ChangeRequest.REQUEST_TYPE_EDIT,
            target_model=ChangeRequest.TARGET_MODEL_CATEGORY,
            target_object_id=obj.pk,
            title=title,
            reason=reason,
            payload=payload,
        )
        cr.save()
        messages.success(self.request, 'Your request has been submitted for moderator approval.')
        return redirect('core:category-list')


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an electrical component category."""
    model = Category
    template_name = 'core/category_confirm_delete.html'
    success_url = reverse_lazy('core:category-list')

    def post(self, request, *args, **kwargs):
        user = request.user
        obj = self.get_object()
        if user.is_staff or user.is_superuser:
            messages.success(request, f"Category '{obj.name}' deleted successfully!")
            return super().post(request, *args, **kwargs)

        reason = normalize_request_reason(request)
        if not reason:
            messages.error(request, 'Reason for deletion request is required.')
            return self.get(request, *args, **kwargs)

        cr = create_change_request(
            user=user,
            request_type=ChangeRequest.REQUEST_TYPE_DELETE,
            target_model=ChangeRequest.TARGET_MODEL_CATEGORY,
            title=str(obj),
            reason=reason,
            target_object_id=obj.pk,
            payload={},
        )
        cr.save()
        messages.success(request, 'Your request has been submitted for moderator approval.')
        return redirect('core:category-list')


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
        context['categories'] = Category.with_components().order_by('name')
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_category'] = self.request.GET.get('category', '')
        return context


class ComponentDetailView(DetailView):
    """Display detailed view of a single electrical component."""
    model = Component
    template_name = 'core/component_detail.html'
    context_object_name = 'component'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Prepare a limited, pre-filtered list of related components to avoid
        # rendering unbounded querysets in the template.
        component = self.object
        related_qs = component.category.components.exclude(id=component.id).order_by('name')
        related_limit = 10
        related_components = list(related_qs[:related_limit])
        related_count = related_qs.count()
        context['related_components'] = related_components
        context['related_count'] = related_count
        context['related_limit'] = related_limit
        return context


class ComponentCreateView(LoginRequiredMixin, CreateView):
    """Create a new electrical component."""
    model = Component
    form_class = ComponentForm
    template_name = 'core/component_form.html'
    success_url = reverse_lazy('core:component-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            messages.success(self.request, f"Component '{form.cleaned_data['name']}' created successfully!")
            return super().form_valid(form)

        reason = normalize_request_reason(self.request)
        if not reason:
            form.add_error(None, 'Reason is required to submit a change request.')
            return self.form_invalid(form)

        payload = normalize_payload(form.cleaned_data)
        # Preserve the raw selection for 'new' category from POST so the
        # change request payload contains the sentinel 'new' string (the
        # models logic looks for that). The form's cleaned_data may have
        # `category` replaced with None to avoid assignment errors, so use
        # the POST value to decide whether this is a new-category request.
        is_new_category = self.request.POST.get('category') == 'new'
        if not is_new_category:
            payload.pop('new_category_name', None)
        else:
            # Ensure payload records the sentinel so approval logic sees it.
            payload['category'] = 'new'

        title = form.cleaned_data.get('name') or 'Create Component'
        cr = create_change_request(
            user=user,
            request_type=ChangeRequest.REQUEST_TYPE_ADD,
            target_model=ChangeRequest.TARGET_MODEL_COMPONENT,
            title=title,
            reason=reason,
            payload=payload,
        )
        cr.save()
        messages.success(self.request, 'Your request has been submitted for moderator approval.')
        return redirect('core:component-list')


class ComponentUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing electrical component."""
    model = Component
    form_class = ComponentForm
    template_name = 'core/component_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy('core:component-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            messages.success(self.request, f"Component '{form.cleaned_data['name']}' updated successfully!")
            return super().form_valid(form)

        reason = normalize_request_reason(self.request)
        if not reason:
            form.add_error(None, 'Reason is required to submit a change request.')
            return self.form_invalid(form)

        obj = self.get_object()
        payload = normalize_payload(form.cleaned_data)
        if payload.get('category') != 'new':
            payload.pop('new_category_name', None)
        title = form.cleaned_data.get('name') or str(obj)
        cr = create_change_request(
            user=user,
            request_type=ChangeRequest.REQUEST_TYPE_EDIT,
            target_model=ChangeRequest.TARGET_MODEL_COMPONENT,
            target_object_id=obj.pk,
            title=title,
            reason=reason,
            payload=payload,
        )
        cr.save()
        messages.success(self.request, 'Your request has been submitted for moderator approval.')
        return redirect('core:component-detail', pk=obj.pk)


class ComponentDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an electrical component."""
    model = Component
    template_name = 'core/component_confirm_delete.html'
    success_url = reverse_lazy('core:component-list')

    def post(self, request, *args, **kwargs):
        user = request.user
        obj = self.get_object()
        if user.is_staff or user.is_superuser:
            messages.success(request, f"Component '{obj.name}' deleted successfully!")
            return super().post(request, *args, **kwargs)

        reason = normalize_request_reason(request)
        if not reason:
            messages.error(request, 'Reason for deletion request is required.')
            return self.get(request, *args, **kwargs)

        cr = create_change_request(
            user=user,
            request_type=ChangeRequest.REQUEST_TYPE_DELETE,
            target_model=ChangeRequest.TARGET_MODEL_COMPONENT,
            title=str(obj),
            reason=reason,
            target_object_id=obj.pk,
            payload={},
        )
        cr.save()
        messages.success(request, 'Your request has been submitted for moderator approval.')
        return redirect('core:component-list')


class InfolectricLoginView(LoginView):
    """Login view using custom authentication form with optional remember me."""
    template_name = 'core/login.html'
    authentication_form = InfolectricAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')
        response = super().form_valid(form)
        if not remember_me:
            self.request.session.set_expiry(0)
        return response


class ProfileView(LoginRequiredMixin, TemplateView):
    """Simple profile page for authenticated Infolectric users."""
    template_name = 'core/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'saved_calculations_count': 0,
            'favorite_components_count': 0,
            'favorite_appliances_count': 0,
            'submission_requests_count': ChangeRequest.objects.filter(user=self.request.user).count(),
        })
        # Ensure the user's profile exists and add to context for templates
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        context['profile'] = profile
        return context


class ProfileEditView(LoginRequiredMixin, TemplateView):
    template_name = 'core/profile_edit.html'

    def get(self, request, *args, **kwargs):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        form = UserProfileForm(initial={})
        return render(request, self.template_name, {'form': form, 'profile': profile})

    def post(self, request, *args, **kwargs):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data.get('remove_image'):
                # delete existing image file
                if profile.profile_image:
                    try:
                        profile.profile_image.delete(save=False)
                    except Exception:
                        pass
                    profile.profile_image = None

            uploaded = form.cleaned_data.get('profile_image')
            if uploaded:
                profile.profile_image = uploaded

            profile.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('core:profile')

        return render(request, self.template_name, {'form': form, 'profile': profile})


def get_request_payload_form(target_model, request_type, data=None, instance=None, initial=None):
    form_mapping = {
        ChangeRequest.TARGET_MODEL_COMPONENT: ComponentRequestPayloadForm,
        ChangeRequest.TARGET_MODEL_APPLIANCE: ApplianceLoadRequestPayloadForm,
        ChangeRequest.TARGET_MODEL_WIRESIZE: WireSizeRequestPayloadForm,
        ChangeRequest.TARGET_MODEL_CATEGORY: CategoryRequestPayloadForm,
    }
    if request_type not in {ChangeRequest.REQUEST_TYPE_ADD, ChangeRequest.REQUEST_TYPE_EDIT}:
        return None
    form_class = form_mapping.get(target_model)
    if not form_class:
        return None
    if data is not None:
        return form_class(data=data, instance=instance, prefix='payload')
    return form_class(prefix='payload', initial=initial)


def _save_uploaded_file_to_storage(uploaded_file):
    filename = os.path.basename(uploaded_file.name)
    unique_name = f"{get_random_string(12)}_{filename}"
    relative_path = os.path.join('change_request_uploads', unique_name).replace('\\', '/')
    default_storage.save(relative_path, uploaded_file)
    return relative_path


def normalize_payload(cleaned_data):
    def normalize_value(value):
        if hasattr(value, 'pk'):
            return value.pk
        if isinstance(value, Decimal):
            return float(value)
        # Uploaded files (InMemoryUploadedFile, TemporaryUploadedFile) are
        # not JSON serializable. Save the file to media and preserve the path.
        if hasattr(value, 'name') and not isinstance(value, (str, bytes)):
            try:
                return {'name': value.name, 'path': _save_uploaded_file_to_storage(value)}
            except Exception:
                return {'name': value.name}
        if isinstance(value, dict):
            return {k: normalize_value(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [normalize_value(v) for v in value]
        return value

    return {key: normalize_value(value) for key, value in cleaned_data.items()}


def normalize_request_reason(request):
    return request.POST.get('reason', '').strip()


def create_change_request(user, request_type, target_model, title, reason='', payload=None, target_object_id=None):
    return ChangeRequest(
        user=user,
        request_type=request_type,
        target_model=target_model,
        target_object_id=target_object_id,
        title=title,
        reason=reason,
        payload=payload or {},
    )


# Legacy request creation removed: CRUD pages now create ChangeRequest entries for non-staff users.


class ChangeRequestListView(LoginRequiredMixin, ListView):
    """Display the authenticated user's request history."""
    model = ChangeRequest
    template_name = 'core/request_list.html'
    context_object_name = 'requests'
    paginate_by = 20

    def get_queryset(self):
        queryset = ChangeRequest.objects.filter(user=self.request.user)
        request_type = self.request.GET.get('request_type', '').strip()
        status = self.request.GET.get('status', '').strip()
        target_model = self.request.GET.get('target_model', '').strip()

        if request_type:
            queryset = queryset.filter(request_type=request_type)
        if status:
            queryset = queryset.filter(status=status)
        if target_model:
            queryset = queryset.filter(target_model=target_model)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_counts'] = {
            status: ChangeRequest.objects.filter(user=self.request.user, status=status).count()
            for status, _ in ChangeRequest.STATUS_CHOICES
        }
        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        context['query_string'] = query_params.urlencode()
        context['request_type_choices'] = ChangeRequest.REQUEST_TYPE_CHOICES
        context['status_choices'] = ChangeRequest.STATUS_CHOICES
        context['target_model_choices'] = ChangeRequest.TARGET_MODEL_CHOICES
        context['results_count'] = self.get_queryset().count()
        return context


class ChangeRequestDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View a single change request detail for users and staff."""
    model = ChangeRequest
    template_name = 'core/request_detail.html'
    context_object_name = 'request_item'

    def test_func(self):
        obj = self.get_object()
        return self.request.user.is_staff or self.request.user.is_superuser or obj.user == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['target_object'] = self.object.get_target_object()
        return context


class ChangeRequestUpdateView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Allow a user to edit the reason on their own pending request."""
    template_name = 'core/request_reason_form.html'

    def get_object(self):
        return get_object_or_404(ChangeRequest, pk=self.kwargs['pk'])

    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user and obj.is_pending()

    def get(self, request, *args, **kwargs):
        change_request = self.get_object()
        form = ChangeRequestReasonForm(instance=change_request)
        return self.render_to_response({
            'form': form,
            'request_item': change_request,
        })

    def post(self, request, *args, **kwargs):
        change_request = self.get_object()
        form = ChangeRequestReasonForm(request.POST, instance=change_request)

        if form.is_valid():
            form.save()
            messages.success(request, 'Your request reason has been updated.')
            return redirect('core:request-detail', pk=change_request.pk)

        return self.render_to_response({
            'form': form,
            'request_item': change_request,
        })


class ChangeRequestCancelView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Allow users to cancel their own pending request."""
    template_name = 'core/request_detail.html'

    def get_object(self):
        return get_object_or_404(ChangeRequest, pk=self.kwargs['pk'])

    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user and obj.is_pending()

    def post(self, request, *args, **kwargs):
        change_request = self.get_object()
        change_request.cancel()
        messages.success(request, 'Your request has been cancelled.')
        return redirect('core:request-detail', pk=change_request.pk)


class RequestModerationListView(ManagementPermissionMixin, ListView):
    """Admin view to filter and browse all change requests."""
    model = ChangeRequest
    template_name = 'core/moderation_list.html'
    context_object_name = 'requests'
    paginate_by = 25

    def get_queryset(self):
        queryset = ChangeRequest.objects.all()
        request_type = self.request.GET.get('request_type')
        status = self.request.GET.get('status')
        target_model = self.request.GET.get('target_model')
        user_query = self.request.GET.get('user')

        if request_type:
            queryset = queryset.filter(request_type=request_type)
        if status:
            queryset = queryset.filter(status=status)
        if target_model:
            queryset = queryset.filter(target_model=target_model)
        if user_query:
            queryset = queryset.filter(user__username__icontains=user_query)

        return queryset.select_related('user', 'approved_by', 'rejected_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'request_types': ChangeRequest.REQUEST_TYPE_CHOICES,
            'statuses': ChangeRequest.STATUS_CHOICES,
            'target_models': ChangeRequest.TARGET_MODEL_CHOICES,
            'filter_values': {
                'request_type': self.request.GET.get('request_type', ''),
                'status': self.request.GET.get('status', ''),
                'target_model': self.request.GET.get('target_model', ''),
                'user': self.request.GET.get('user', ''),
            }
        })
        # Group pending requests by type for quick review
        base_qs = ChangeRequest.objects.filter(status=ChangeRequest.STATUS_PENDING)
        context['pending_create_requests'] = base_qs.filter(request_type=ChangeRequest.REQUEST_TYPE_ADD).select_related('user')
        context['pending_edit_requests'] = base_qs.filter(request_type=ChangeRequest.REQUEST_TYPE_EDIT).select_related('user')
        context['pending_delete_requests'] = base_qs.filter(request_type=ChangeRequest.REQUEST_TYPE_DELETE).select_related('user')
        return context


class RequestModerationDetailView(ManagementPermissionMixin, DetailView):
    """Review a single change request and approve or reject it."""
    model = ChangeRequest
    template_name = 'core/moderation_detail.html'
    context_object_name = 'request_item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['target_object'] = self.object.get_target_object()
        context['admin_form'] = RequestAdminForm(instance=self.object)
        return context


class ChangeRequestAdminUpdateView(ManagementPermissionMixin, UpdateView):
    """Allow admin to edit a pending request before approval."""
    model = ChangeRequest
    form_class = RequestAdminForm
    template_name = 'core/request_admin_form.html'

    def get_success_url(self):
        return reverse_lazy('core:moderation-request-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Request details updated successfully.')
        return super().form_valid(form)


class RequestApproveView(ManagementPermissionMixin, TemplateView):
    """Approve a pending request."""
    template_name = 'core/moderation_detail.html'

    def post(self, request, *args, **kwargs):
        change_request = get_object_or_404(ChangeRequest, pk=self.kwargs['pk'])
        admin_notes = request.POST.get('admin_notes', '')
        try:
            change_request.approve(request.user, notes=admin_notes)
            messages.success(request, 'Request approved and changes applied successfully.')
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect('core:moderation-request-detail', pk=change_request.pk)


class RequestRejectView(ManagementPermissionMixin, TemplateView):
    """Reject a pending request."""
    template_name = 'core/moderation_detail.html'

    def post(self, request, *args, **kwargs):
        change_request = get_object_or_404(ChangeRequest, pk=self.kwargs['pk'])
        admin_notes = request.POST.get('admin_notes', '')
        try:
            change_request.reject(request.user, notes=admin_notes)
            messages.success(request, 'Request rejected successfully.')
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect('core:moderation-request-detail', pk=change_request.pk)


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
        user = self.request.user
        if user.is_staff or user.is_superuser:
            messages.success(
                self.request,
                f"Wire size {form.cleaned_data['wire_size_mm2']}mm² created successfully!"
            )
            return super().form_valid(form)

        reason = normalize_request_reason(self.request)
        if not reason:
            form.add_error(None, 'Reason is required to submit a change request.')
            return self.form_invalid(form)

        payload = normalize_payload(form.cleaned_data)
        title = f"Wire size {form.cleaned_data.get('wire_size_mm2')}mm²"
        cr = create_change_request(
            user=user,
            request_type=ChangeRequest.REQUEST_TYPE_ADD,
            target_model=ChangeRequest.TARGET_MODEL_WIRESIZE,
            title=title,
            reason=reason,
            payload=payload,
        )
        cr.save()
        messages.success(self.request, 'Your request has been submitted for moderator approval.')
        return redirect('core:wiresize-list')


class WireSizeUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing wire size specification."""
    model = WireSize
    form_class = WireSizeForm
    template_name = 'core/wiresize_form.html'

    def get_success_url(self):
        return reverse_lazy('core:wiresize-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            messages.success(
                self.request,
                f"Wire size {form.cleaned_data['wire_size_mm2']}mm² updated successfully!"
            )
            return super().form_valid(form)

        reason = normalize_request_reason(self.request)
        if not reason:
            form.add_error(None, 'Reason is required to submit a change request.')
            return self.form_invalid(form)

        obj = self.get_object()
        payload = normalize_payload(form.cleaned_data)
        title = f"Wire size {form.cleaned_data.get('wire_size_mm2')}mm²"
        cr = create_change_request(
            user=user,
            request_type=ChangeRequest.REQUEST_TYPE_EDIT,
            target_model=ChangeRequest.TARGET_MODEL_WIRESIZE,
            target_object_id=obj.pk,
            title=title,
            reason=reason,
            payload=payload,
        )
        cr.save()
        messages.success(self.request, 'Your request has been submitted for moderator approval.')
        return redirect('core:wiresize-detail', pk=obj.pk)


class WireSizeDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a wire size specification."""
    model = WireSize
    template_name = 'core/wiresize_confirm_delete.html'
    success_url = reverse_lazy('core:wiresize-list')

    def post(self, request, *args, **kwargs):
        user = request.user
        obj = self.get_object()
        if user.is_staff or user.is_superuser:
            messages.success(request, f"Wire size {obj.wire_size_mm2}mm² deleted successfully!")
            return super().post(request, *args, **kwargs)

        reason = normalize_request_reason(request)
        if not reason:
            messages.error(request, 'Reason for deletion request is required.')
            return self.get(request, *args, **kwargs)

        cr = create_change_request(
            user=user,
            request_type=ChangeRequest.REQUEST_TYPE_DELETE,
            target_model=ChangeRequest.TARGET_MODEL_WIRESIZE,
            title=str(obj),
            reason=reason,
            target_object_id=obj.pk,
            payload={},
        )
        cr.save()
        messages.success(request, 'Your request has been submitted for moderator approval.')
        return redirect('core:wiresize-list')


# ============================================================================
# GENERAL VIEWS
# ============================================================================

def index(request):
    """Homepage view with overview of the platform."""
    context = {
        'component_count': Component.objects.count(),
        'category_count': Category.objects.count(),
        'wiresize_count': WireSize.objects.count(),
        'appliance_count': ApplianceLoad.objects.count(),
        'recent_components': Component.objects.all()[:5],
    }
    return render(request, 'core/index.html', context)


def register(request):
    """Registration page for new users."""
    form = UserRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        auth_login(request, user)
        messages.success(request, 'Welcome to Infolectric! Your account has been created.')
        return redirect('core:index')

    return render(request, 'core/register.html', {'form': form})


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
                usage_type = explorer_form.cleaned_data['usage_type']
                wire_length = explorer_form.cleaned_data.get('wire_length')
                try:
                    capability = services.get_wire_capability(
                        wire_size=wire_size,
                        wire_length=wire_length,
                        usage_type=usage_type
                    )
                    compatible_appliances = services.get_compatible_appliances(wire_size, usage_type=usage_type)
                    safe_combinations = services.generate_safe_combinations(wire_size, usage_type=usage_type)
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
                wire_length = form.cleaned_data.get('wire_length') or Decimal('10')

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
                        first_wire = recommendations[0]
                        selected_wire_size = Decimal(first_wire['wire_size_mm2'])
                        selected_wire_max_ampacity = Decimal(first_wire['max_ampacity'])
                        resistance = services.calculate_wire_resistance(selected_wire_size, wire_length)
                        voltage_value = voltage or Decimal('220')
                        voltage_drop = services.calculate_voltage_drop(current_value, resistance)
                        voltage_drop_percent = services.calculate_voltage_drop_percent(voltage_value, voltage_drop)
                        power_loss = services.calculate_power_loss(current_value, resistance)
                        efficiency = services.calculate_efficiency(voltage_value, voltage_drop)
                        load_voltage = services.calculate_load_voltage(voltage_value, voltage_drop)
                        max_power = selected_wire_max_ampacity * voltage_value
                        warning = services.get_voltage_drop_warning(voltage_drop_percent)

                        result = {
                            'power_watts': services.format_decimal(power or Decimal('0'), 2) if power is not None else None,
                            'voltage': services.format_decimal(voltage_value, 2),
                            'current': services.format_decimal(current_value, 3),
                            'adjusted_current': services.format_decimal(adjusted_current, 3),
                            'wire_length': services.format_decimal(wire_length, 2),
                            'selected_wire_size': str(selected_wire_size),
                            'selected_wire_max_ampacity': services.format_decimal(selected_wire_max_ampacity, 2),
                            'max_power': services.format_decimal(max_power, 2),
                            'resistance': services.format_decimal(resistance, 5),
                            'voltage_drop': services.format_decimal(voltage_drop, 3),
                            'voltage_drop_percent': services.format_decimal(voltage_drop_percent, 2),
                            'load_voltage': services.format_decimal(load_voltage, 2),
                            'power_loss': services.format_decimal(power_loss, 2),
                            'efficiency': services.format_decimal(efficiency, 2),
                            'warning': warning,
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
                'power_watts': services.format_decimal(services.to_decimal(power), 2),
                'voltage': services.format_decimal(services.to_decimal(voltage), 2),
                'current': services.format_decimal(current, 3),
                'adjusted_current': services.format_decimal(adjusted, 3),
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
        user = self.request.user
        if user.is_staff or user.is_superuser:
            messages.success(self.request, f"Appliance '{form.cleaned_data['name']}' created successfully!")
            return super().form_valid(form)

        reason = normalize_request_reason(self.request)
        if not reason:
            form.add_error(None, 'Reason is required to submit a change request.')
            return self.form_invalid(form)

        payload = normalize_payload(form.cleaned_data)
        title = form.cleaned_data.get('name') or 'Create Appliance'
        cr = create_change_request(
            user=user,
            request_type=ChangeRequest.REQUEST_TYPE_ADD,
            target_model=ChangeRequest.TARGET_MODEL_APPLIANCE,
            title=title,
            reason=reason,
            payload=payload,
        )
        cr.save()
        messages.success(request, 'Your request has been submitted for moderator approval.')
        return redirect('core:appliance-list')


class ApplianceUpdateView(LoginRequiredMixin, UpdateView):
    model = ApplianceLoad
    form_class = ApplianceLoadForm
    template_name = 'core/appliance_form.html'

    def get_success_url(self):
        return reverse_lazy('core:appliance-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            messages.success(self.request, f"Appliance '{form.cleaned_data['name']}' updated successfully!")
            return super().form_valid(form)

        reason = normalize_request_reason(self.request)
        if not reason:
            form.add_error(None, 'Reason is required to submit a change request.')
            return self.form_invalid(form)

        obj = self.get_object()
        payload = normalize_payload(form.cleaned_data)
        title = form.cleaned_data.get('name') or str(obj)
        cr = create_change_request(
            user=user,
            request_type=ChangeRequest.REQUEST_TYPE_EDIT,
            target_model=ChangeRequest.TARGET_MODEL_APPLIANCE,
            target_object_id=obj.pk,
            title=title,
            reason=reason,
            payload=payload,
        )
        cr.save()
        messages.success(self.request, 'Your request has been submitted for moderator approval.')
        return redirect('core:appliance-detail', pk=obj.pk)


class ApplianceDeleteView(LoginRequiredMixin, DeleteView):
    model = ApplianceLoad
    template_name = 'core/appliance_confirm_delete.html'
    success_url = reverse_lazy('core:appliance-list')

    def post(self, request, *args, **kwargs):
        user = request.user
        obj = self.get_object()
        if user.is_staff or user.is_superuser:
            messages.success(request, f"Appliance '{obj.name}' deleted successfully!")
            return super().post(request, *args, **kwargs)

        reason = normalize_request_reason(request)
        if not reason:
            messages.error(request, 'Reason for deletion request is required.')
            return self.get(request, *args, **kwargs)

        cr = create_change_request(
            user=user,
            request_type=ChangeRequest.REQUEST_TYPE_DELETE,
            target_model=ChangeRequest.TARGET_MODEL_APPLIANCE,
            title=str(obj),
            reason=reason,
            target_object_id=obj.pk,
            payload={},
        )
        cr.save()
        messages.success(request, 'Your request has been submitted for moderator approval.')
        return redirect('core:appliance-list')


def ProjectBuilderView(request):
    """Select multiple appliances to summarise and get recommendations."""
    form = ProjectBuilderForm(request.POST or None)
    output = None
    error = None
    if request.method == 'POST' and form.is_valid():
        appliances = form.cleaned_data['appliances']
        total_power = sum((services.to_decimal(a.power_watts or 0) for a in appliances), Decimal('0'))
        voltage = services.to_decimal(appliances.first().voltage or Decimal('230'))
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
