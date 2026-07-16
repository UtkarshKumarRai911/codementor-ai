"""Database models for the CodeMentor AI API."""

from django.contrib.auth.models import User
from django.db import models


class Query(models.Model):
    """Represents a user query to the CodeMentor AI system."""

    class QueryType(models.TextChoices):
        DEBUG = "debug", "Debug Code"
        EXPLAIN = "explain", "Explain Code"
        GENERATE = "generate", "Generate Code"
        OPTIMIZE = "optimize", "Optimize Code"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    # User relationship
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="queries")

    # Input fields
    question = models.TextField(help_text="The user's question or request")
    code_snippet = models.TextField(blank=True, default="", help_text="Code provided by the user")
    language = models.CharField(
        max_length=50, blank=True, default="python", help_text="Programming language"
    )
    error_message = models.TextField(
        blank=True, default="", help_text="Error message if debugging"
    )
    query_type = models.CharField(
        max_length=20, choices=QueryType.choices, default=QueryType.DEBUG
    )

    # Status
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    # Response fields
    explanation = models.TextField(blank=True, default="")
    fixed_code = models.TextField(blank=True, default="")
    similar_problems = models.JSONField(default=list, blank=True)
    retrieved_context = models.JSONField(default=list, blank=True)

    # Metrics
    processing_time_ms = models.IntegerField(null=True, blank=True)
    retrieval_time_ms = models.IntegerField(null=True, blank=True)
    tokens_used = models.IntegerField(null=True, blank=True)
    model_used = models.CharField(max_length=100, blank=True, default="")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "queries"
        indexes = [
            models.Index(fields=["-created_at"], name="api_query_created_idx"),
            models.Index(
                fields=["user", "-created_at"],
                name="api_query_user_created_idx",
            ),
            models.Index(fields=["query_type"], name="api_query_type_idx"),
            models.Index(fields=["status"], name="api_query_status_idx"),
        ]

    def __str__(self) -> str:
        return f"Query({self.id}) by {self.user.username}: {self.question[:50]}..."


class Feedback(models.Model):
    """User feedback on query responses."""

    class Rating(models.IntegerChoices):
        VERY_POOR = 1, "Very Poor"
        POOR = 2, "Poor"
        AVERAGE = 3, "Average"
        GOOD = 4, "Good"
        EXCELLENT = 5, "Excellent"

    query = models.OneToOneField(Query, on_delete=models.CASCADE, related_name="feedback")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="feedbacks")
    rating = models.IntegerField(choices=Rating.choices)
    comment = models.TextField(blank=True, default="")
    is_code_correct = models.BooleanField(null=True, blank=True)
    is_explanation_helpful = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Feedback({self.id}) for Query({self.query_id}): {self.rating}/5"
