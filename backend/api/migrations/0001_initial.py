# Generated for CodeMentor AI initial deployment.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Query",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question", models.TextField(help_text="The user's question or request")),
                ("code_snippet", models.TextField(blank=True, default="", help_text="Code provided by the user")),
                ("language", models.CharField(blank=True, default="python", help_text="Programming language", max_length=50)),
                ("error_message", models.TextField(blank=True, default="", help_text="Error message if debugging")),
                ("query_type", models.CharField(choices=[("debug", "Debug Code"), ("explain", "Explain Code"), ("generate", "Generate Code"), ("optimize", "Optimize Code")], default="debug", max_length=20)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("processing", "Processing"), ("completed", "Completed"), ("failed", "Failed")], default="pending", max_length=20)),
                ("explanation", models.TextField(blank=True, default="")),
                ("fixed_code", models.TextField(blank=True, default="")),
                ("similar_problems", models.JSONField(blank=True, default=list)),
                ("retrieved_context", models.JSONField(blank=True, default=list)),
                ("processing_time_ms", models.IntegerField(blank=True, null=True)),
                ("retrieval_time_ms", models.IntegerField(blank=True, null=True)),
                ("tokens_used", models.IntegerField(blank=True, null=True)),
                ("model_used", models.CharField(blank=True, default="", max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="queries", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name_plural": "queries", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Feedback",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rating", models.IntegerField(choices=[(1, "Very Poor"), (2, "Poor"), (3, "Average"), (4, "Good"), (5, "Excellent")])),
                ("comment", models.TextField(blank=True, default="")),
                ("is_code_correct", models.BooleanField(blank=True, null=True)),
                ("is_explanation_helpful", models.BooleanField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("query", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="feedback", to="api.query")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="feedbacks", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="query",
            index=models.Index(fields=["-created_at"], name="api_query_created_idx"),
        ),
        migrations.AddIndex(
            model_name="query",
            index=models.Index(fields=["user", "-created_at"], name="api_query_user_created_idx"),
        ),
        migrations.AddIndex(
            model_name="query",
            index=models.Index(fields=["query_type"], name="api_query_type_idx"),
        ),
        migrations.AddIndex(
            model_name="query",
            index=models.Index(fields=["status"], name="api_query_status_idx"),
        ),
    ]
