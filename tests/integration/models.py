from django.db import models


class IntegrationAuthor(models.Model):
    class Meta:
        app_label = "optimizer_integration"
        db_table = "dio_integration_author"


class IntegrationBook(models.Model):
    author = models.ForeignKey(
        IntegrationAuthor,
        on_delete=models.CASCADE,
        db_constraint=False,
    )
    published_at = models.DateTimeField(null=True)

    class Meta:
        app_label = "optimizer_integration"
        db_table = "dio_integration_book"
