from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='generator_index'),
    url(r'^gallery$', views.gallery, name='gallery'),
]
