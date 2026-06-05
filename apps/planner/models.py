from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=255, verbose_name="Project Name")
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_completed(self) -> bool:
        return (
                self.places.exists() and
                not self.places.filter(is_visited=False).exists()
        )

    def __str__(self):
        return self.name


class Place(models.Model):
    project = models.ForeignKey(Project, related_name='places', on_delete=models.CASCADE)
    external_id = models.CharField(max_length=255, verbose_name="Art Institute API ID")
    notes = models.TextField(blank=True, null=True)
    is_visited = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "external_id"],
                name="unique_project_place"
            )
        ]

        indexes = [
            models.Index(fields=["is_visited"]),
            models.Index(fields=["external_id"]),
        ]

    def __str__(self):
        return f"Place {self.external_id} in {self.project.name}"