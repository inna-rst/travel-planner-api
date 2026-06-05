import httpx
import logging
from typing import Optional
from django.core.cache import cache

logger = logging.getLogger(__name__)

class ArtInstituteAPIError(Exception):
    pass


class ArtInstituteAPIClient:
    BASE_URL = "https://api.artic.edu/api/v1"
    CACHE_TIMEOUT = 60 * 60  # 1 hour
    FIELDS = "id,title,date_display,artist_display,place_of_origin,image_id"

    @classmethod
    def get_artwork(cls, external_id: int) -> Optional[dict]:
        cache_key = f"artic:artwork:{external_id}"
        cached = cache.get(cache_key)
        if cached is not None:
            logger.debug("Cache hit for artwork %s", external_id)
            return cached

        url = f"{cls.BASE_URL}/artworks/{external_id}"
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url, params={"fields": cls.FIELDS})

            if response.status_code == 404:
                return None

            response.raise_for_status()
            data = response.json().get("data", {})
            cache.set(cache_key, data, cls.CACHE_TIMEOUT)
            return data

        except httpx.TimeoutException:
            logger.error("Timeout fetching artwork %s", external_id)
            raise ArtInstituteAPIError("Art Institute API timed out. Please try again later.")
        except httpx.RequestError as exc:
            logger.error("Connection error fetching artwork %s: %s", external_id, exc)
            raise ArtInstituteAPIError(f"Cannot reach Art Institute API: {exc}")

    @classmethod
    def search_artworks(cls, query: str, page: int = 1, limit: int = 10) -> dict:
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(
                    f"{cls.BASE_URL}/artworks/search",
                    params={
                        "q": query,
                        "page": page,
                        "limit": limit,
                        "fields": "id,title,date_display,artist_display",
                    },
                )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise ArtInstituteAPIError(str(exc))
