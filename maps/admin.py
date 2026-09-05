from django.contrib import admin
from .models import SchoolMetadata

@admin.register(SchoolMetadata)
class SchoolMetadataAdmin(admin.ModelAdmin):
    list_display = ('school_name', 'updated_at')
    search_fields = ('school_name',)