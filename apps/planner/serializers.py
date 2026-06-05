from rest_framework import serializers
from django.db import transaction
from .models import Project, Place
from .services import ArtInstituteAPIClient


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ['id', 'project', 'external_id', 'notes', 'is_visited', 'added_at']
        read_only_fields = ['id', 'added_at']
        extra_kwargs = {
            'project': {'required': False}
        }

        validators = []

    def validate_external_id(self, value):
        if self.instance and self.instance.external_id == value:
            return value

        if not ArtInstituteAPIClient.validate_place(value):
            raise serializers.ValidationError(
                f"Place with ID '{value}' does not exist in Art Institute API."
            )
        return value

class ProjectSerializer(serializers.ModelSerializer):
    places = PlaceSerializer(many=True, required=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'start_date', 'is_completed', 'created_at', 'places']
        read_only_fields = ['id', 'is_completed', 'created_at']

    def validate_places(self, value):
        if not value:
            raise serializers.ValidationError(
                "Project must contain at least 1 place."
            )

        if len(value) > 10:
            raise serializers.ValidationError("A project can have a maximum of 10 places.")

        external_ids = [place.get('external_id') for place in value if place.get('external_id')]
        if len(external_ids) != len(set(external_ids)):
            raise serializers.ValidationError("Duplicate places in the request are not allowed.")

        return value

    def create(self, validated_data):
        places_data = validated_data.pop('places', [])

        with transaction.atomic():
            project = Project.objects.create(**validated_data)

            for place_data in places_data:
                external_id = place_data.get('external_id')

                if not ArtInstituteAPIClient.validate_place(external_id):
                    raise serializers.ValidationError({
                        "places": f"Place with ID '{external_id}' does not exist in Art Institute API."
                    })

                Place.objects.create(project=project, **place_data)

        return project

    def update(self, instance, validated_data):
        validated_data.pop('places', None)
        return super().update(instance, validated_data)