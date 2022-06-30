from functools import partial
from random import choices

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from django.contrib.auth.validators import UnicodeUsernameValidator

from main.models import LawyerCase, LawyersSchema, LawyersClientsSchema, Bill


DateInput = partial(forms.DateInput, {'class': 'datepicker'})


class MyUsernameValidator(UnicodeUsernameValidator):
    regex = r'^[\w -]+\Z'
    message = _('הכנס שם תקין. שם תקין מורכב מאותיות, רווחים ומקף')


class RegisterForm(UserCreationForm):
    error_messages = {
        'password_mismatch': _('שתי הסיסמאות לא תואמות.')
    }

    class Meta:
        model = User
        fields = ["first_name", "last_name", "password1", "password2"]


class AddLawyerCaseForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user_lawyers = [(i.lawyer, f'{i.lawyer.first_name} {i.lawyer.last_name}') for i in LawyersSchema.objects.filter(admin=user)]
        self.fields['lawyer'] = forms.models.ModelChoiceField(queryset=User.objects.filter(pk__in=[user_lawyer[0].pk for user_lawyer in user_lawyers]))
        self.fields['lawyer_client'] = forms.ChoiceField(choices=[("", "---------")])

        lawyer_id = None
        if 'lawyer' in self.data:
            try:
                lawyer_id = int(self.data['lawyer'])
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            lawyer_id = self.instance.lawyer.pk

        self.fields['lawyer_client'].choices += [(client.client, client.client) for client in LawyersClientsSchema.objects.filter(lawyer__pk=lawyer_id)]

    class Meta:
        model = LawyerCase
        fields = ['deliver_type', 'lawyer_case_id', 'client_name', 'client_id', 'client_address', 'notes', 'file', 'deliver_file', 'deliver_man_name']


class UpdateLawyerCaseForm(forms.ModelForm):
    READ_ONLY_FIELDS = ['user', 'lawyer', 'lawyer_client', 'status', 'deliver_type', 'lawyer_case_id', 'client_name', 'client_id']
    EXCLUDE_FOR_LAWYERS = ['deliver_man_name', 'deliver_address', 'deliver_to', 'status', 'notes', 'deliver_file']

    def __init__(self, is_lawyer, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if is_lawyer:
            for field in self.fields.keys():
                if field in self.EXCLUDE_FOR_LAWYERS:
                    del self.fields[field]
                elif field != 'file':
                    self.fields[field].widget.attrs['readonly'] = True
        else:
            del self.fields['file']
            for field in self.READ_ONLY_FIELDS:
                self.fields[field].widget.attrs['readonly'] = True

    class Meta:
        model = LawyerCase
        exclude = ['close_date', 'open_date']


class UpdateLawyerCaseCloseForm(forms.ModelForm):
    READ_ONLY_FIELDS = ['user', 'lawyer', 'lawyer_client', 'status', 'deliver_type', 'lawyer_case_id', 'client_name', 'client_id']

    close_date = forms.DateField(widget=DateInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.READ_ONLY_FIELDS:
            self.fields[field].widget.attrs['readonly'] = True

        self.fields['close_date'].required = True
        self.fields['deliver_file'].required = True

    class Meta:
        model = LawyerCase
        exclude = ['close_date', 'open_date', 'file']


class SearchLawyerCaseForm(forms.ModelForm):
    case_id = forms.IntegerField()
    start_date = forms.DateField(widget=DateInput())
    end_date = forms.DateField(widget=DateInput())

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        lawyer_admins = [i.admin for i in LawyersSchema.objects.filter(lawyer=user)]
        self.fields['user'].queryset = User.objects.filter(pk__in=[lawyer_admin.pk for lawyer_admin in lawyer_admins])

        user_lawyers = [i.lawyer for i in LawyersSchema.objects.filter(admin=user)]
        self.fields['lawyer'].queryset = User.objects.filter(pk__in=[user_lawyer.pk for user_lawyer in user_lawyers])

        self.fields['lawyer_client'] = forms.ChoiceField(choices=[("", "---------")])

        lawyer_id = None
        if 'lawyer' in self.data:
            try:
                lawyer_id = int(self.data['lawyer'])
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            lawyer_id = self.instance.lawyer.pk
        elif not user.userprofile.is_groupadmin:
            lawyer_id = user.pk

        self.fields['lawyer_client'].choices += [(client.client, client.client) for client in LawyersClientsSchema.objects.filter(lawyer__pk=lawyer_id)]

        for field in self.fields.keys():
            self.fields[field].required = False
            self.fields[field].initial = None

    class Meta:
        model = LawyerCase
        exclude = ['file', 'deliver_file', 'close_date', 'open_date', 'notes', 'lawyer_client']


class LawyersClientsSchemaForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user_lawyers = [i.lawyer for i in LawyersSchema.objects.filter(admin=user)]
        self.fields['lawyer'].queryset = User.objects.filter(pk__in=[user_lawyer.pk for user_lawyer in user_lawyers])
    
    class Meta:
        model = LawyersClientsSchema
        exclude = []
