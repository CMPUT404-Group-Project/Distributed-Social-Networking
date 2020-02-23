from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from .models import Author


class AuthorAdmin(UserAdmin):
    model = Author

    list_display = ('displayName', 'first_name', 'last_name', 'email', 'is_active', 'is_staff')
    search_fields = ('displayName', 'first_name', 'last_name', 'email')
    readonly_fields = ('id', 'host', 'url', 'displayName', 'date_joined', 'last_login', )

    filter_horizontal = ()
    ordering = ()
    list_filter = ()
    fieldsets = ()

admin.site.register(Author, AuthorAdmin)