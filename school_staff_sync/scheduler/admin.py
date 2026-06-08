from django.contrib import admin
from .models import Profile, Schedule, Availability

admin.site.register(Profile)
admin.site.register(Schedule)
admin.site.register(Availability)