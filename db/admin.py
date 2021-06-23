from django.contrib import admin
from django.apps import apps


class BaseModelAdmin(admin.ModelAdmin):
    readonly_fields = (
        'date_created',
        'date_modified'
    )


app = apps.get_app_config('db')
for model_name, model in app.models.items():
    admin.site.register(model, BaseModelAdmin)
