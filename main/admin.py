from django.contrib import admin
from main.models import UserProfile, LawyerCase, LawyersSchema, LawyersClientsSchema

admin.site.register(UserProfile)
admin.site.register(LawyerCase)
admin.site.register(LawyersSchema)
admin.site.register(LawyersClientsSchema)
