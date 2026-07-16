"""URL configuration for the CodeMentor AI API."""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

app_name = "api"

urlpatterns = [
    # Authentication
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/profile/", views.ProfileView.as_view(), name="profile"),
    # Queries
    path("query/submit/", views.QuerySubmitView.as_view(), name="query_submit"),
    path("query/history/", views.QueryHistoryView.as_view(), name="query_history"),
    path("query/stats/", views.query_stats, name="query_stats"),
    path("query/<int:pk>/", views.QueryDetailView.as_view(), name="query_detail"),
    # Feedback
    path("feedback/", views.FeedbackView.as_view(), name="feedback"),
    # Health
    path("health/", views.health_check, name="health_check"),
]
