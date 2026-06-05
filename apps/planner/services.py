import httpx
import logging
from django.core.cache import cache
from rest_framework.exceptions import ValidationError
from .models import Project


logger = logging.getLogger(__name__)


def delete_project(project: Project) -> None:
    if project.places.filter(is_visited=True).exists():
        raise ValidationError({"detail": "Cannot delete project: it contains visited places."})

    project.delete()


class ArtInstituteAPIClient:
    BASE_URL = "https://api.artic.edu/api/v1"
    CACHE_TIMEOUT = 60 * 60 * 24

    @classmethod
    def validate_place(cls, external_id: str) -> bool:
        if not external_id:
            return False

        cache_key = f"artic_api_place_{external_id}"

        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        url = f"{cls.BASE_URL}/artworks/{external_id}"

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url)
                is_valid = response.status_code == 200

            cache.set(cache_key, is_valid, cls.CACHE_TIMEOUT)
            return is_valid

        except httpx.RequestError as exc:
            logger.error(f"Error connecting to Art Institute API for {external_id}: {exc}")
            return False