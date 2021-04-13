from django.urls import include
from django.urls import path

from . import views

urlpatterns = [
    path('api/', include('web.routing')),

    path('', views.IndexView.as_view(), name='index'),

    path('search/', views.SearchView.as_view(), name='search'),

    path('results/<worksheet>/<sample>',
         views.SampleDetailsView.as_view(), name='sample_details'),


    path('ajax/load_worksheet_details/<int:pk>',
         views.load_worksheet_details, name='load_worksheet_details'),

    path('ajax/update_selected_transcript/<int:sample>/<int:transcript>',
         views.update_selected_transcript, name='update_selected_transcript'),

    path('ajax/load_variant_details/<int:variant>',
         views.load_variant_details, name='load_variant_details'),

    path('ajax/save_evidence/<int:stv>',
         views.save_evidence, name='save_evidence'),

    # Temporary to explore jbrowse during development
    path('jbrowse-testing', views.JbrowseTestingView.as_view(),
         name='jbrowse-testing')
]
