"""API Serializers for the CodeMentor AI system."""

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Feedback, Query


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password_confirm"]

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data: dict) -> User:
        validated_data.pop("password_confirm")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile information."""

    total_queries = serializers.SerializerMethodField()
    member_since = serializers.DateTimeField(source="date_joined", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "total_queries", "member_since"]
        read_only_fields = ["id", "username", "total_queries", "member_since"]

    def get_total_queries(self, obj: User) -> int:
        return obj.queries.count()


class QuerySubmitSerializer(serializers.Serializer):
    """Serializer for submitting a new query."""

    question = serializers.CharField(max_length=5000)
    code_snippet = serializers.CharField(required=False, default="", allow_blank=True)
    language = serializers.CharField(max_length=50, required=False, default="python")
    error_message = serializers.CharField(required=False, default="", allow_blank=True)
    query_type = serializers.ChoiceField(
        choices=Query.QueryType.choices, default=Query.QueryType.DEBUG
    )


class QueryResponseSerializer(serializers.ModelSerializer):
    """Serializer for query response data."""

    has_feedback = serializers.SerializerMethodField()

    class Meta:
        model = Query
        fields = [
            "id",
            "question",
            "code_snippet",
            "language",
            "error_message",
            "query_type",
            "status",
            "explanation",
            "fixed_code",
            "similar_problems",
            "retrieved_context",
            "processing_time_ms",
            "retrieval_time_ms",
            "tokens_used",
            "model_used",
            "has_feedback",
            "created_at",
            "updated_at",
        ]

    def get_has_feedback(self, obj: Query) -> bool:
        return hasattr(obj, "feedback")


class QueryHistorySerializer(serializers.ModelSerializer):
    """Serializer for query history (lightweight)."""

    class Meta:
        model = Query
        fields = [
            "id",
            "question",
            "query_type",
            "language",
            "status",
            "processing_time_ms",
            "created_at",
        ]


class FeedbackSerializer(serializers.ModelSerializer):
    """Serializer for user feedback."""

    class Meta:
        model = Feedback
        fields = [
            "id",
            "query",
            "rating",
            "comment",
            "is_code_correct",
            "is_explanation_helpful",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_query(self, value: Query) -> Query:
        request = self.context.get("request")
        if request and value.user != request.user:
            raise serializers.ValidationError("You can only provide feedback on your own queries.")
        if hasattr(value, "feedback"):
            raise serializers.ValidationError("Feedback already exists for this query.")
        return value
