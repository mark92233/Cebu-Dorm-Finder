from django.db import models

class SchoolMetadata(models.Model):
    """
    Stores enriched data about schools, fetched from external sources like Wikipedia
    and processed by AI. This data is pre-loaded or fetched on-demand to be
    displayed quickly on the map interface.
    """
    school_name = models.CharField(max_length=255, unique=True, primary_key=True)
    summary = models.TextField(blank=True, null=True)
    image_url = models.URLField(max_length=1024, blank=True, null=True)
    source_url = models.URLField(max_length=1024, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.school_name

class FacebookPost(models.Model):
    """
    Stores raw, sanitized text payloads from scraped Facebook housing groups.
    This model acts as the first stage in the data ingestion pipeline for listings.
    """
    post_url = models.URLField(max_length=255, unique=True, primary_key=True, help_text="The direct URL to the Facebook post.")
    post_content = models.TextField(help_text="The sanitized, full text content of the post.")
    source_group = models.CharField(max_length=255, help_text="The name or identifier of the Facebook group where the post was found.")
    scraped_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp of when this post was processed by the AI pipeline.")

    class Meta:
        ordering = ['-scraped_at']

    def __str__(self):
        return self.post_url