from django.contrib import admin

# Register your models here.
from .models import user_registration

admin.site.register(user_registration)