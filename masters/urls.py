from django.urls import path
from .views import (
    FirmMasterListCreateAPIView,
    FirmMasterDetailAPIView,
    GroupMasterListCreateAPIView,
    GroupMasterDetailAPIView,
    GroupCategoriesAPIView,
    LedgerMasterListCreateAPIView,
    LedgerMasterDetailAPIView,
)

urlpatterns = [
    # Firm Master Endpoints
    path('firms/', FirmMasterListCreateAPIView.as_view(), name='firm-master-list'),
    path('firms/<str:pk>/', FirmMasterDetailAPIView.as_view(), name='firm-master-detail'),

    # Group Master Endpoints
    path('groups/', GroupMasterListCreateAPIView.as_view(), name='group-master-list'),
    path('groups/categories/', GroupCategoriesAPIView.as_view(), name='group-categories'),
    path('groups/<int:pk>/', GroupMasterDetailAPIView.as_view(), name='group-master-detail'),

    # Ledger Master Endpoints
    path('ledgers/', LedgerMasterListCreateAPIView.as_view(), name='ledger-master-list'),
    path('ledgers/<str:pk>/', LedgerMasterDetailAPIView.as_view(), name='ledger-master-detail'),
]
