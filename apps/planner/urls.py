from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, PlaceViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'places', PlaceViewSet, basename='place')

urlpatterns = [
    path('', include(router.urls)),
]