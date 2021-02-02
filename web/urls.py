from django.urls import path

from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),

    path('search', views.SearchView.as_view(), name='search'),

    path('sample', views.SampleView.as_view(), name='sample'),

    path('ajax/load_variant_details',
         views.load_variant_details, name='load_variant_details'),
    path('ajax/save_evidence',
         views.save_evidence, name='save_evidence')
]
