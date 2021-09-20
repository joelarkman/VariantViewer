from django import template
from db.models import Run

register = template.Library()


@register.filter
def get_classification_colour(run, index):
    run = Run.objects.get(id=run)
    return run.pipeline_version.classification_options[index]['colour']
