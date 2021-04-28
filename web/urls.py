from django.urls import include
from django.urls import path

from . import views

urlpatterns = [
    path('api/', include('web.routing')),

    path('', views.IndexView.as_view(), name='index'),

    path('search/', views.SearchView.as_view(), name='search'),

    path('results/<worksheet>/<sample>',
         views.SampleDetailsView.as_view(), name='sample_details'),


    ######################
    ##### AJAX VIEWS #####
    ######################

    # temp
    path('ajax/load_worksheet_details/<int:pk>',
         views.load_worksheet_details, name='load_worksheet_details'),

    path('ajax/modify_filters/<int:run>/<int:ss_sample>/<filter>',
         views.modify_filters, name='modify_filters'),

    path('ajax/update_selected_transcript/<int:run>/<int:ss_sample>/<int:transcript>',
         views.update_selected_transcript, name='update_selected_transcript'),

    path('ajax/load_variant_details/<int:run>/<int:stv>',
         views.load_variant_details, name='load_variant_details'),

    path('ajax/pin_variant/<int:run>/<int:stv>',
         views.pin_variant, name='pin_variant'),

    path('ajax/comment_update_or_create/<int:stv>',
         views.comment_update_or_create, name='comment_update_or_create'),

    path('ajax/save_evidence/<int:stv>',
         views.save_evidence, name='save_evidence'),

    # Temporary to explore jbrowse during development
    path('jbrowse-testing', views.JbrowseTestingView.as_view(),
         name='jbrowse-testing')
]
