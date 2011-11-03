from django.contrib import admin

from cc.profile.models import Profile, Settings

class SettingsInline(admin.StackedInline):
    model = Settings

class ProfileAdmin(admin.ModelAdmin):
    inlines = (SettingsInline,)

admin.site.register(Profile, ProfileAdmin)
