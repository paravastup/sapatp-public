from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Plant, Pattern, Universe, AuditEntry, SearchHistory, Profile
from django.contrib.auth import get_user_model

# Register your models here.
User = get_user_model()

admin.site.register(Pattern)
admin.site.register(Universe)
admin.site.register(Plant)
# <your_app>/admin.py

@admin.register(AuditEntry)
class AuditEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'login_time', 'logout_time', 'host', 'ip']
    list_filter = ['user', 'host', 'ip']


class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['username', 'time', 'referencekey']
    list_filter = ['username','referencekey']


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class PlantInline(admin.TabularInline):
    model = Plant.users.through


def activate_users(modeladmin,request, queryset):
    queryset.update(is_active=True)
activate_users.short_description = "Activate selected users"

def deactivate_users(modeladmin, request, queryset):
    queryset.update(is_active=False)
deactivate_users.short_description = "Deactivate selected users"

class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'date_joined', 'first_name', 'last_name', 'is_active']
    list_editable = ['is_active']
    actions = [activate_users, deactivate_users]
    inlines = (ProfileInline, PlantInline)
    model = User
    def get_inline_instances(self,request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(SearchHistory,SearchHistoryAdmin)
