from django.contrib import admin
from django.apps import apps


class BaseModelAdmin(admin.ModelAdmin):
    readonly_fields = (
        'date_created',
        'date_modified'
    )


admin.site.site_title = 'WMRGL VariantViewer'
admin.site.site_header = 'WMRGL VariantViewer Administration'
admin.site.index_title = 'App administration'

app = apps.get_app_config('web')
for model_name, model in app.models.items():
    admin.site.register(model, BaseModelAdmin)
