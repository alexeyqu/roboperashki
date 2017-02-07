from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^collocations$', views.collocations, name='collocations'),
]
