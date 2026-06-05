import logging
from django.db import transaction, IntegrityError
from django.db.models import Exists, OuterRef, Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.db.models import Count, Exists, OuterRef, Case, When, Value, BooleanField

from .models import Project, Place
from .serializers import (
    ProjectSerializer,
    ProjectListSerializer,
    ProjectCreateSerializer,
    ProjectUpdateSerializer,
    PlaceSerializer,
    PlaceAddSerializer,
    PlaceUpdateSerializer,
)
from .services import ArtInstituteAPIClient, ArtInstituteAPIError

logger = logging.getLogger(__name__)
MAX_PLACES_PER_PROJECT = 10


class ProjectViewSet(viewsets.ModelViewSet):
    def get_queryset(self):

        qs = Project.objects.annotate(places_count=Count("places"))

        has_places = Exists(Place.objects.filter(project=OuterRef("pk")))
        has_unvisited = Exists(Place.objects.filter(project=OuterRef("pk"), is_visited=False))

        qs = qs.annotate(
            _has_places=has_places,
            _has_unvisited=has_unvisited,
            is_completed=Case(
                When(_has_places=True, _has_unvisited=False, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        )

        is_completed_param = self.request.query_params.get("is_completed")
        if is_completed_param is not None:
            if is_completed_param.lower() == "true":
                qs = qs.filter(is_completed=True)
            else:
                qs = qs.filter(is_completed=False)

        name = self.request.query_params.get("name")
        if name:
            qs = qs.filter(name__icontains=name)

        if self.action == "retrieve":
            qs = qs.prefetch_related("places")

        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return ProjectListSerializer
        if self.action == "create":
            return ProjectCreateSerializer
        if self.action in ("update", "partial_update"):
            return ProjectUpdateSerializer
        return ProjectSerializer  # retrieve

    def create(self, request, *args, **kwargs):
        serializer = ProjectCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        places_data = validated_data.pop("places", [])

        artworks_to_save = []
        for item in places_data:
            artwork = self._fetch_artwork_or_raise(item["external_id"])
            artworks_to_save.append({
                "external_id": item["external_id"],
                "artwork": artwork
            })

        project = self._create_project_in_db(validated_data, artworks_to_save)

        out = ProjectSerializer(project, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def _create_project_in_db(self, project_data: dict, artworks_data: list) -> Project:
        project = Project.objects.create(**project_data)

        if artworks_data:
            to_create = [
                Place(
                    project=project,
                    external_id=item["external_id"],
                    title=item["artwork"].get("title", ""),
                    artwork_data=item["artwork"],
                )
                for item in artworks_data
            ]
            Place.objects.bulk_create(to_create)

        return Project.objects.prefetch_related("places").get(pk=project.pk)


    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        if project.places.filter(is_visited=True).exists():
            return Response(
                {"detail": "Cannot delete a project that contains visited places."},
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)

    def _fetch_artwork_or_raise(self, external_id: int) -> dict:
        try:
            artwork = ArtInstituteAPIClient.get_artwork(external_id)
        except ArtInstituteAPIError as exc:
            raise ValidationError({"places": f"Art Institute API error: {exc}"})
        if artwork is None:
            raise ValidationError({
                "places": (
                    f"Artwork {external_id} not found in the Art Institute of Chicago API."
                )
            })
        return artwork


class PlaceViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return (
            Place.objects
            .filter(project_id=self.kwargs["project_pk"])
            .select_related("project")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return PlaceAddSerializer
        if self.action in ("update", "partial_update"):
            return PlaceUpdateSerializer
        return PlaceSerializer


    def create(self, request, *args, **kwargs):

        serializer = PlaceAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        external_id: int = serializer.validated_data["external_id"]

        try:
            artwork = ArtInstituteAPIClient.get_artwork(external_id)
        except ArtInstituteAPIError as exc:
            raise ValidationError({"external_id": f"Art Institute API error: {exc}"})

        if artwork is None:
            raise ValidationError({"external_id": f"Artwork {external_id} not found."})

        with transaction.atomic():
            project = get_object_or_404(Project.objects.select_for_update(), pk=self.kwargs["project_pk"])

            current_count = Place.objects.filter(project=project).count()
            if current_count >= MAX_PLACES_PER_PROJECT:
                raise ValidationError({"detail": f"Max {MAX_PLACES_PER_PROJECT} places reached."})

            try:
                place = Place.objects.create(
                    project=project,
                    external_id=external_id,
                    title=artwork.get("title", ""),
                    artwork_data=artwork,
                )
            except IntegrityError:
                raise ValidationError({"external_id": f"Artwork {external_id} is already in this project."})

        return Response(PlaceSerializer(place).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        place = self.get_object()
        serializer = PlaceUpdateSerializer(place, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(PlaceSerializer(serializer.instance).data)
