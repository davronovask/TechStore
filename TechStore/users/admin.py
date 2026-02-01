from django.contrib import admin
from .models import User, PendingUser

# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'email',
        'phone_number',
        'first_name',
        'last_name',
    ]

@admin.register(PendingUser)
class PendingUserAdmin(admin.ModelAdmin):
    list_display = [
        'email',
        'phone_number',
        'verification_code',
        'register_at',
    ]
