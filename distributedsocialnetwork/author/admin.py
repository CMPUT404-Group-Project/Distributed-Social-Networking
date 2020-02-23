from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from .forms import AuthorCreationForm, AuthorChangeForm
from .models import Author


class AuthorAdmin(UserAdmin):
    model = Author

    add_form = AuthorCreationForm
    form = AuthorChangeForm

    list_display = ('displayName', 'first_name', 'last_name', 'email', 'is_active', 'is_staff')
    list_filter = ('is_active',)
    search_fields = ('displayName', 'first_name', 'last_name', 'email')
    readonly_fields = ('id', 'host', 'url', 'displayName', 'date_joined', 'last_login', 'username')

    filter_horizontal = ()
    ordering = ()

    fieldsets = (
        (None, {
            'fields':(
                'displayName',
                'email',
                'first_name',
                'last_name',
                'github',
                'is_active',
                'is_staff',
                'host',
                'id',
                'url',
                'date_joined',
                'last_login'
            )
        }),
    )

admin.site.register(Author, AuthorAdmin)