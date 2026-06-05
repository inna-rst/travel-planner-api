from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, PlaceViewSet

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")

place_list = PlaceViewSet.as_view({"get": "list", "post": "create"})
place_detail = PlaceViewSet.as_view({"get": "retrieve", "patch": "partial_update"})

urlpatterns = [
    path("", include(router.urls)),
    path(
        "projects/<int:project_pk>/places/",
        place_list,
        name="project-place-list",
    ),
    path(
        "projects/<int:project_pk>/places/<int:pk>/",
        place_detail,
        name="project-place-detail",
    ),
]

