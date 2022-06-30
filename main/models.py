from tabnanny import verbose
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.models import User
from django.forms import ValidationError
from django.urls import reverse
from django.db import models
from django.utils.translation import gettext as _
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_israel_id(value):
    if type(value) != str:
        raise ValidationError('value must be string: %(value_type)', params={'value_type': type(value)})

    MIN_ID_LEN = 8
    MAX_ID_LEN = 9
    if MIN_ID_LEN > len(value) and MAX_ID_LEN < len(value):
        raise ValidationError('מספר ת"ז חייב להכיל 8-9 ספרות.')

    value = value.zfill(9)
    id_sum = 0
    for i, digit in enumerate(value):
        if i % 2 != 0:
            digit = str(int(digit) * 2)

        while len(digit) > 1:
            digit = str(int(digit[0]) + int(digit[1]))

        id_sum += int(digit)

    if id_sum % 10 != 0:
        raise ValidationError('מספר ת"ז אינו תקין.')


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_groupadmin = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _("userprofile")
        verbose_name_plural = _("userprofiles")

    def __str__(self):
        return f'{self.user.username} profile'


class LawyersSchema(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name=_('admin'))
    lawyer = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name=_('client_lawyer'))

    class Meta:
        verbose_name = _("lawyersschema")
        verbose_name_plural = _("lawyersschemas")

    def __str__(self):
        return f'{self.admin.username} -> {self.lawyer.username}'


class LawyersClientsSchema(models.Model):
    lawyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name=_("lawyer_client"))
    client = models.CharField(max_length=50)

    class Meta:
        verbose_name = _("lawyerclientsschema")
        verbose_name_plural = _("lawyerclientsschemas")

    def __str__(self):
        return f'{self.lawyer.username} -> {self.client}'


class Bill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name=_('bill_user'))
    lawyer = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name=_('bill_lawyer'))
    lawyer_pay = models.IntegerField()
    delivery_pay = models.IntegerField()
    find_pay = models.IntegerField()

    class Meta:
        verbose_name = _("bill")
        verbose_name_plural = _("bills")

    def __str__(self):
        return str(self.pk)


class LawyerCase(models.Model):
    DeliverType = ( ('NOTICE', _('התראה')),
                    ('WARNING', _('אזהרה')),
                    ('JUDGEMENT', _('פסק דין')),
                    ('CLAIM_STATEMENT', _('כתב תביעה')),
                    ('SUBMISSION', _('הגשה')))

    StatusType = (  ('Received', _('התקבל')),
                    ('Delivered', _('נמסר')),
                    ('Canceled', _('התבטל')))

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name=_('user'))
    lawyer = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name=_('lawyer'))
    lawyer_client = models.CharField(max_length=50)
    deliver_type = models.CharField(choices=DeliverType, max_length=260, blank=False, null=False)
    lawyer_case_id = models.CharField(max_length=20, blank=False, null=False, validators=[RegexValidator(regex=r'\d+', message='מספר תיק חייב להכיל רק ספרות.')])
    client_name = models.CharField(max_length=50, blank=False, null=False)
    client_id = models.CharField(max_length=9, blank=False, null=False, validators=[validate_israel_id])
    client_address = models.CharField(max_length=260, default='', blank=True)
    deliver_man_name = models.CharField(max_length=260, blank=False, null=False)
    deliver_address = models.CharField(max_length=260, blank=True, default='')
    deliver_to = models.CharField(max_length=20, blank=True, default='')
    status = models.CharField(choices=StatusType, max_length=20, blank=False, null=False)
    notes = models.TextField(max_length=1024, default='', blank=True)
    open_date = models.DateField(null=False, default=timezone.now)
    close_date = models.DateField(null=True, blank=True, default=None)
    file = models.FileField(null=True, blank=True, default=None)
    deliver_file = models.FileField(null=True, blank=True, default=None)
    bill = models.ForeignKey(Bill, on_delete=models.DO_NOTHING, null=True, blank=True, default=None)

    class Meta:
        ordering = ('-open_date', '-pk')
        verbose_name = _("lawyercase")
        verbose_name_plural = _("lawyercases")

    def __str__(self):
        return f'{self.user.username} -> {self.lawyer.username} case number: {self.lawyer_case_id}'


