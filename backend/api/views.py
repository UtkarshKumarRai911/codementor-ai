"""API Views for the CodeMentor AI system."""

import logging
import time

from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Feedback, Query
from .serializers import (
    FeedbackSerializer,
    QueryHistorySerializer,
    QueryResponseSerializer,
    QuerySubmitSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
)

logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    """User registration endpoint."""

    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "User registered successfully.",
                "user": {"id": user.id, "username": user.username, "email": user.email},
            },
            status=status.HTTP_201_CREATED,
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    """User profile endpoint."""

    serializer_class = UserProfileSerializer

    def get_object(self) -> User:
        return self.request.user


class QuerySubmitView(generics.CreateAPIView):
    """Submit a new query to the multi-agent pipeline."""

    serializer_class = QuerySubmitSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create query record
        query = Query.objects.create(
            user=request.user,
            question=serializer.validated_data["question"],
            code_snippet=serializer.validated_data.get("code_snippet", ""),
            language=serializer.validated_data.get("language", "python"),
            error_message=serializer.validated_data.get("error_message", ""),
            query_type=serializer.validated_data.get("query_type", Query.QueryType.DEBUG),
            status=Query.Status.PROCESSING,
        )

        start_time = time.time()

        try:
            # Run the multi-agent pipeline
            from agents.graph import run_agent_pipeline

            result = run_agent_pipeline(
                question=query.question,
                code_snippet=query.code_snippet,
                language=query.language,
                error_message=query.error_message,
                query_type=query.query_type,
            )

            # Update query with results
            processing_time = int((time.time() - start_time) * 1000)
            query.explanation = result.get("explanation", "")
            query.fixed_code = result.get("fixed_code", "")
            query.similar_problems = result.get("similar_problems", [])
            query.retrieved_context = result.get("retrieved_context", [])
            query.processing_time_ms = processing_time
            query.retrieval_time_ms = result.get("retrieval_time_ms")
            query.tokens_used = result.get("tokens_used")
            query.model_used = result.get("model_used", "")
            query.status = Query.Status.COMPLETED
            query.save()

            logger.info(
                f"Query {query.id} completed in {processing_time}ms "
                f"(tokens: {query.tokens_used})"
            )

        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            query.status = Query.Status.FAILED
            query.explanation = f"An error occurred: {str(e)}"
            query.processing_time_ms = processing_time
            query.save()
            logger.error(f"Query {query.id} failed: {str(e)}", exc_info=True)

        response_serializer = QueryResponseSerializer(query)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class QueryHistoryView(generics.ListAPIView):
    """List user's query history."""

    serializer_class = QueryHistorySerializer

    def get_queryset(self):
        return Query.objects.filter(user=self.request.user)


class QueryDetailView(generics.RetrieveAPIView):
    """Get detailed query response."""

    serializer_class = QueryResponseSerializer

    def get_queryset(self):
        return Query.objects.filter(user=self.request.user)


class FeedbackView(generics.CreateAPIView):
    """Submit feedback for a query response."""

    serializer_class = FeedbackSerializer

    def perform_create(self, serializer: FeedbackSerializer) -> None:
        serializer.save(user=self.request.user)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def health_check(request: Request) -> Response:
    """Health check endpoint for monitoring."""
    return Response(
        {
            "status": "healthy",
            "service": "codementor-ai",
            "version": "1.0.0",
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def query_stats(request: Request) -> Response:
    """Get query statistics for the authenticated user."""
    user_queries = Query.objects.filter(user=request.user)

    stats = {
        "total_queries": user_queries.count(),
        "completed_queries": user_queries.filter(status=Query.Status.COMPLETED).count(),
        "failed_queries": user_queries.filter(status=Query.Status.FAILED).count(),
        "avg_processing_time_ms": user_queries.filter(
            status=Query.Status.COMPLETED
        ).aggregate(avg=Avg("processing_time_ms"))["avg"],
        "queries_by_type": dict(
            user_queries.values_list("query_type").annotate(count=Count("id")).values_list(
                "query_type", "count"
            )
        ),
        "queries_by_language": dict(
            user_queries.values_list("language")
            .annotate(count=Count("id"))
            .values_list("language", "count")[:10]
        ),
        "avg_feedback_rating": Feedback.objects.filter(user=request.user).aggregate(
            avg=Avg("rating")
        )["avg"],
    }

    return Response(stats, status=status.HTTP_200_OK)
