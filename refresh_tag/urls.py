from django.urls import path
from .views import get_refresh_tag

urlpatterns = [
    path('get-refresh-tag/', get_refresh_tag, name='get_refresh_tag'),
]
