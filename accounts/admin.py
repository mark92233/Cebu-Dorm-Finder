from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile

# Register your models here.

class UserProfileInline(admin.StackedInline):
    """
    Defines an inline admin descriptor for UserProfile model,
    which can be used to display and edit profile information
    directly in the User admin page.
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'

class UserAdmin(BaseUserAdmin):
    """
    Extends the default User admin to include the UserProfile inline.
    """
    # The fields to be used in displaying the User model in the admin list.
    # We override the defaults to use fields that exist on our custom User model.
    list_display = ('email', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('email',)
    ordering = ('email',)

    # The fieldsets to be used in the user change page.
    # We must override this to remove 'username', 'first_name', 'last_name'.
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    inlines = (UserProfileInline,)

# Re-register UserAdmin
admin.site.register(User, UserAdmin)
