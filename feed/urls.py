# ============================================================
# SPORTLINK — URLs Feed
# ============================================================

from django.urls import path
from .views import FeedView

urlpatterns = [
    # GET — Feed de découverte style TikTok
    path('feed/', FeedView.as_view(), name='feed'),
]