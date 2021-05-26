from django.urls import include
from django.urls import path

from . import views

urlpatterns = [
    path('api/', include('web.routing')),

    path('', views.RedirectView.as_view(), kwargs={
         'update': False}, name='redirect'),
    path('section-update', views.RedirectView.as_view(),
         kwargs={'update': True}, name='change_section'),

    path('<slug:section>', views.HomeView.as_view(), name='home'),

    path('<slug:section>/search/', views.SearchView.as_view(), name='search'),

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

    path('ajax/load_variant_list/<int:run>/<int:ss_sample>',
         views.load_variant_list, name='load_variant_list'),

    path('ajax/load_variant_details/<int:run>/<int:stv>',
         views.load_variant_details, name='load_variant_details'),

    path('ajax/pin_variant/<int:run>/<int:stv>',
         views.pin_variant, name='pin_variant'),

    path('ajax/comment_update_or_create/<int:stv>',
         views.comment_update_or_create, name='comment_update_or_create'),

    path('ajax/save_evidence/<int:stv>',
         views.save_evidence, name='save_evidence'),

    path('ajax/archive_evidence/<int:document>',
         views.archive_evidence, name='archive_evidence'),

    path('ajax/load_previous_evidence/<int:current_stv>/<int:previous_stv>',
         views.load_previous_evidence, name='load_previous_evidence'),

    # Temporary to explore jbrowse during development
    path('jbrowse-testing', views.JbrowseTestingView.as_view(),
         name='jbrowse-testing')
]
