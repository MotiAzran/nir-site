import os
from sre_constants import SUCCESS

from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import Group, Permission
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import View, CreateView, ListView, DeleteView, DetailView, UpdateView

from main.models import Bill, LawyerCase, LawyersClientsSchema, UserProfile, LawyersSchema
from main.forms import AddLawyerCaseForm, LawyersClientsSchemaForm, RegisterForm, SearchLawyerCaseForm, UpdateLawyerCaseForm, UpdateLawyerCaseCloseForm

"""
TODO:
Move bar to side - Done
Add date range on search - Done
Lawyer only add file to case - Done
Add close_date to close case - Done
Add file on close case - Done
Edit case - Done
Add clients to lawyers - Done
Add clients dynamically to lawyers - Done
Add cases to bill
Edit bill
Add bills to doh
Add case action
"""


def get_clients(request):
    lawyer_id = request.GET.get('lawyer')
    
    clients_list = []
    if lawyer_id and lawyer_id != '':
        clients_list = [client.client for client in LawyersClientsSchema.objects.filter(lawyer__pk=int(lawyer_id))]
    
    return render(request, 'main/hr/clients_dropdown_list.html', {'clients': clients_list})


class LoginRequired(LoginRequiredMixin):
    login_url = '/login/'


class RegisterView(UserPassesTestMixin, View):
    form_class = RegisterForm
    template_name = 'main/register.html'

    NEW_GROUP_PERMS = ['add_lawyercase', 'delete_lawyercase', 'view_lawyercase']
    NEW_GROUP_ADMIN_PERMS = ['add_user', 'change_user', 'delete_user', 'view_user']

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.userprofile.is_groupadmin

    def create_new_group(self, name):
        group = Group.objects.create(name=name)
        group.permissions.add(*[Permission.objects.get(codename=perm) for perm in self.NEW_GROUP_PERMS])

        return group

    def set_new_group_admin(self, user):
        user.user_permissions.add(*[Permission.objects.get(codename=perm) for perm in self.NEW_GROUP_ADMIN_PERMS])
        user.userprofile.is_groupadmin = True
        user.userprofile.save()

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        form.instance.username = f'{request.POST["first_name"].replace(" ", "-")}-{request.POST["last_name"].replace(" ", "-")}'
        if form.is_valid():
            new_user = form.save()
            UserProfile.objects.create(user=new_user)

            user_group = None
            try:
                if request.user.is_superuser:
                    user_group = self.create_new_group(form.instance.username)
                    self.set_new_group_admin(new_user)
                else:
                    LawyersSchema.objects.create(admin=request.user, lawyer=new_user)
                    user_group = self.request.user.groups.first()

                new_user.groups.add(user_group)
                form.save()
                form = self.form_class(None)
            except:
                new_user.delete()
                if request.user.is_superuser and user_group is not None:
                    user_group.delete()

                raise

        return render(request, self.template_name, {'form': form})


class LawyerCasesView(LoginRequired, ListView):
    model = LawyerCase
    template_name = 'main/show_cases.html'
    context_object_name = 'cases_list'
    paginate_by = 10

    def filter_cases(self, cases):
        post_fields = ['deliver_type', 'lawyer_case_id', 'client_name', 'client_id', 'client_address', 'deliver_man_name', 'deliver_address', 'status']
        kwargs = dict()
        if self.request.user.userprofile.is_groupadmin:
            lawyer_pk = self.request.POST['lawyer']
            if lawyer_pk != '':
                kwargs['lawyer__pk'] = int(lawyer_pk)

            case_id = self.request.POST['case_id']
            if case_id != '':
                kwargs['id'] = int(case_id)
        else:
            user_pk = self.request.POST['user']
            if user_pk != '':
                kwargs['user__pk'] = int(user_pk)

        start_date = self.request.POST['start_date']
        if start_date != '':
            d, m, y = start_date.split('/')
            kwargs['open_date__gte'] = f'{y}-{m}-{d}'

        end_date = self.request.POST['end_date']
        if end_date != '':
            d, m, y = end_date.split('/')
            kwargs['open_date__lte'] = f'{y}-{m}-{d}'

        for field in post_fields:
            value = self.request.POST[field]
            if value != '':
                kwargs[field] = value

        cases = cases.filter(**kwargs)

        return cases

    def get_group_cases(self, group):
        cases_ids = []
        for user in group.user_set.all():
            cases_ids += [case.pk for case in LawyerCase.objects.filter(lawyer=user)]

        return LawyerCase.objects.filter(pk__in=cases_ids)

    def get_queryset(self):
        self._search_form = SearchLawyerCaseForm(self.request.user)
        cases = LawyerCase.objects.none()
        cur_user = self.request.user
        if cur_user.userprofile.is_groupadmin:
            cases = self.get_group_cases(cur_user.groups.first())
        else:
            cases = LawyerCase.objects.filter(lawyer=cur_user)

        if self.request.method == 'POST':
            if 'case_file' not in self.request.FILES:
                cases = self.filter_cases(cases)
            
            self._search_form = SearchLawyerCaseForm(self.request.user, self.request.POST)

        return cases

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self._search_form
        context['title'] = 'תיקים קיימים'

        return context

    def post(self, request, *args, **kwargs):
        if 'case_file' in request.FILES:
            case = get_object_or_404(LawyerCase, pk=int(request.POST['case_id']))
            case.file = request.FILES['case_file']
            case.save()

        return super().get(request, *args, **kwargs)


class LawyerCaseCreate(UserPassesTestMixin, LoginRequired, CreateView):
    model = LawyerCase
    form_class = AddLawyerCaseForm
    success_url = reverse_lazy('home')
    template_name = 'main/add_case.html'

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.userprofile.is_groupadmin

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        
        return kwargs

    def form_valid(self, form):
        if self.request.user.userprofile.is_groupadmin:
            form.instance.user = self.request.user
            form.instance.lawyer = form.cleaned_data['lawyer']
        else:
            form.instance.lawyer = self.request.user
            form.instance.user = form.cleaned_data['user']

        form.instance.status = 'Received'
        return super().form_valid(form)


class LawyerCaseUpdate(LoginRequired, UserPassesTestMixin, UpdateView):
    model = LawyerCase
    form_class = UpdateLawyerCaseForm
    success_url = reverse_lazy('home')
    template_name = 'main/edit_case.html'

    def test_func(self):
        obj = self.get_object()
        return self.request.user == obj.lawyer or self.request.user == obj.user

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, pk=self.kwargs['case_id'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_lawyer'] = False

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['case'] = self.get_object()

        return context

    def form_valid(self, form):
        return super().form_valid(form)


class LawyerCaseCloseUpdate(LoginRequired, UserPassesTestMixin, UpdateView):
    model = LawyerCase
    form_class = UpdateLawyerCaseCloseForm
    success_url = reverse_lazy('home')
    template_name = 'main/close_case.html'

    def test_func(self):
        obj = self.get_object()
        return self.request.user == obj.lawyer or self.request.user == obj.user

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, pk=self.kwargs['case_id'])

    def form_valid(self, form):
        if form.instance.close_date:
            return super.form_valid(form)

        form.instance.status = 'Delivered'
        return super().form_valid(form)


class LawyerCaseCancel(UserPassesTestMixin, LoginRequired, UpdateView):
    model = LawyerCase
    success_url = reverse_lazy('home')

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.userprofile.is_groupadmin

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, pk=self.kwargs['case_id'])

    def post(self, request):
        case = get_object_or_404(self.model, pk=int(request.POST['case_id']))
        if request.user != case.lawyer and request.user != case.user:
            return HttpResponseForbidden()

        case.status = 'Canceled'
        case.save()

        return redirect(self.success_url)


class LawyerCaseView(LoginRequired, DetailView):
    model = LawyerCase
    template_name = 'main/case.html'

    def post(self, request):
        lawyercase = get_object_or_404(self.model, pk=int(request.POST['case_id']))
        return render(request, self.template_name, {'lawyercase': lawyercase})


class LawyerCaseDelete(UserPassesTestMixin, LoginRequired, DeleteView):
    model = LawyerCase
    success_url = reverse_lazy('home')

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.userprofile.is_groupadmin

    def post(self, request):
        case_to_delete = get_object_or_404(self.model, pk=int(request.POST['case_id']))
        if request.user != case_to_delete.lawyer and request.user != case_to_delete.user:
            return HttpResponseForbidden()

        case_to_delete.file.delete()
        case_to_delete.deliver_file.delete()
        case_to_delete.delete()
        return redirect(self.success_url)


class DownloadCaseFile(LoginRequired, View):
    def get(seld, request, case_id):
        case_to_download = get_object_or_404(LawyerCase, pk=case_id)
        if request.user != case_to_download.lawyer and request.user != case_to_download.user:
            return HttpResponseForbidden()

        if case_to_download.file:
            path = case_to_download.file.path
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type="application/vnd.ms-excel")
                    response['Content-Disposition'] = 'inline; filename=' + os.path.basename(path)
                    return response
        
        return HttpResponseNotFound()


class DownloadCaseApproveFile(LoginRequired, View):
    def get(seld, request, case_id):
        case_to_download = get_object_or_404(LawyerCase, pk=case_id)
        if request.user != case_to_download.lawyer and request.user != case_to_download.user:
            return HttpResponseForbidden()

        if case_to_download.deliver_file:
            path = case_to_download.deliver_file.path
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type="application/vnd.ms-excel")
                    response['Content-Disposition'] = 'inline; filename=' + os.path.basename(path)
                    return response
        
        return HttpResponseNotFound()


class AddLawyerClient(LoginRequired, UserPassesTestMixin, CreateView):
    model = LawyersClientsSchema
    form_class = LawyersClientsSchemaForm
    success_url = reverse_lazy('home')
    template_name = 'main/add_lawyer_client.html'

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.userprofile.is_groupadmin

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        
        return kwargs


class AddBill(LoginRequired, UserPassesTestMixin, CreateView):
    model = Bill
    form_class = SearchLawyerCaseForm
    success_url = reverse_lazy("home")
    template_name = 'main/add_bill.html'
    paginate_by = 10

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.userprofile.is_groupadmin

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        
        return kwargs
