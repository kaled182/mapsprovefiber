from django.urls import path
from . import views

app_name = 'routes_builder'

urlpatterns = [
    path('fiber-route-builder/', views.fiber_route_builder_view, name='fiber_route_builder'),
]
