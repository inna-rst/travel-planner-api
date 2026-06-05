from django.db import models
from django.utils import timezone


class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    start_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name


class Place(models.Model):
    project = models.ForeignKey(
        Project, related_name="places", on_delete=models.CASCADE
    )
    external_id = models.PositiveIntegerField()
    title = models.CharField(max_length=500, default="")
    artwork_data = models.JSONField(default=dict)
    notes = models.TextField(blank=True, default="")
    is_visited = models.BooleanField(default=False)
    visited_at = models.DateTimeField(null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "external_id"],
                name="unique_project_place",
            )
        ]
        indexes = [
            models.Index(fields=["is_visited"]),
            models.Index(fields=["external_id"]),
        ]
        ordering = ["added_at"]

    def mark_as_visited(self) -> None:
        if not self.is_visited:
            self.is_visited = True
            self.visited_at = timezone.now()
            self.save(update_fields=["is_visited", "visited_at", "updated_at"])

    def __str__(self) -> str:
        return f"{self.title} — {self.project.name}"
