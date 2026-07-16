"""Admin configuration for the CodeMentor AI API."""

from django.contrib import admin

from .models import Feedback, Query


@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    """Admin interface for Query model."""

    list_display = [
        "id",
        "user",
        "query_type",
        "language",
        "status",
        "processing_time_ms",
        "created_at",
    ]
    list_filter = ["query_type", "status", "language", "created_at"]
    search_fields = ["question", "user__username", "explanation"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]

    fieldsets = (
        ("User Info", {"fields": ("user",)}),
        ("Input", {"fields": ("question", "code_snippet", "language", "error_message", "query_type")}),
        ("Status", {"fields": ("status",)}),
        ("Response", {"fields": ("explanation", "fixed_code", "similar_problems", "retrieved_context")}),
        ("Metrics", {"fields": ("processing_time_ms", "retrieval_time_ms", "tokens_used", "model_used")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    """Admin interface for Feedback model."""

    list_display = ["id", "query", "user", "rating", "is_code_correct", "is_explanation_helpful", "created_at"]
    list_filter = ["rating", "is_code_correct", "is_explanation_helpful", "created_at"]
    search_fields = ["comment", "user__username"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]
