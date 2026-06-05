from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django_filters.rest_framework import DjangoFilterBackend

from .models import Project, Place
from .serializers import ProjectSerializer, PlaceSerializer
from .services import ArtInstituteAPIClient, delete_project


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.prefetch_related('places').all()
    serializer_class = ProjectSerializer

    filter_backends = [DjangoFilterBackend]

    filterset_fields = {
        'name': ['icontains'],
        'start_date': ['exact', 'gte', 'lte'],
    }

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        delete_project(project)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        queryset = super().get_queryset()

        is_completed_param = self.request.query_params.get('is_completed')

        if is_completed_param is not None:
            is_completed = is_completed_param.lower() == 'true'

            from django.db.models import Exists, OuterRef, Q

            unvisited_places = Place.objects.filter(
                project=OuterRef('pk'),
                is_visited=False
            )

            queryset = queryset.annotate(
                has_unvisited=Exists(unvisited_places),
                has_places=Exists(Place.objects.filter(project=OuterRef('pk')))
            )

            if is_completed:
                queryset = queryset.filter(has_unvisited=False, has_places=True)
            else:
                queryset = queryset.filter(Q(has_unvisited=True) | Q(has_places=False))

        return queryset

class PlaceViewSet(viewsets.ModelViewSet):
    queryset = Place.objects.select_related('project').all()
    serializer_class = PlaceSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project', 'is_visited']

    def perform_create(self, serializer):
        project_id = self.request.data.get('project')
        if not project_id:
            raise ValidationError({"project": ["This field is required for a single place."]})

        with transaction.atomic():
            try:
                project = Project.objects.select_for_update().get(pk=project_id)
            except Project.DoesNotExist:
                raise ValidationError({"project": ["Project not found."]})

            if project.places.count() >= 10:
                raise ValidationError({"detail": "Maximum of 10 places per project reached."})


            serializer.save(project=project)


