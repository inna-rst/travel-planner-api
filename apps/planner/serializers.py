from typing import Optional
from rest_framework import serializers
from .models import Project, Place
from django.utils import timezone

class PlaceSerializer(serializers.ModelSerializer):
    artwork_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = [
            "id", "external_id", "title",
            "notes", "is_visited", "visited_at",
            "artwork_image_url", "added_at",
        ]

    def get_artwork_image_url(self, obj: Place) -> Optional[str]:
        image_id = obj.artwork_data.get("image_id")
        if image_id:
            return f"https://www.artic.edu/iiif/2/{image_id}/full/843,/0/default.jpg"
        return None


class PlaceAddSerializer(serializers.Serializer):
    external_id = serializers.IntegerField(min_value=1)


class PlaceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ["notes", "is_visited"]

    def validate_is_visited(self, value: bool) -> bool:
        # Бизнес-правило: место нельзя "отменить" как посещённое.
        if self.instance and self.instance.is_visited and not value:
            raise serializers.ValidationError(
                "Cannot unmark a visited place."
            )
        return value

    def update(self, instance: Place, validated_data: dict) -> Place:
        if validated_data.get("is_visited") and not instance.is_visited:
            instance.is_visited = True
            instance.visited_at = timezone.now()
            validated_data.pop("is_visited", None)
        return super().update(instance, validated_data)

class ProjectListSerializer(serializers.ModelSerializer):
    is_completed = serializers.BooleanField(read_only=True)
    places_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Project
        fields = [
            "id", "name", "description", "start_date",
            "is_completed", "places_count",
            "created_at", "updated_at",
        ]


class ProjectSerializer(serializers.ModelSerializer):
    is_completed = serializers.BooleanField(read_only=True)
    places = PlaceSerializer(many=True, read_only=True)
    places_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Project
        fields = [
            "id", "name", "description", "start_date",
            "is_completed", "places_count", "places",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "is_completed", "created_at", "updated_at"]


class ProjectCreateSerializer(serializers.ModelSerializer):
    places = PlaceAddSerializer(many=True, required=True, allow_empty=False)

    class Meta:
        model = Project
        fields = ["name", "description", "start_date", "places"]

    def validate_places(self, value: list) -> list:
        if len(value) > 10:
            raise serializers.ValidationError(
                f"A project can have at most 10 places. Got {len(value)}."
            )
        ids = [p["external_id"] for p in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Duplicate external_id values in places list.")
        return value


class ProjectUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["name", "description", "start_date"]
