from django.urls import include
from django.urls import path
from rest_framework import routers

from web import endpoints

# RESTful API
router = routers.DefaultRouter()
router.register('(?P<section>.+)/sample_list',
                endpoints.SampleListView, basename='SamplesheetSample')
router.register('(?P<section>.+)/runs_awaiting_first_check_list',
                endpoints.RunsAwaitingFirstCheckListView, basename='Run')
router.register('(?P<section>.+)/runs_awaiting_second_check_list',
                endpoints.RunsAwaitingSecondCheckListView, basename='Run')

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
