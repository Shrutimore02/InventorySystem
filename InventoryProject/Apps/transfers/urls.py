from django.urls import path
from .views import (
    ApproveTransferView,
    CancelTransferView,
    ConfirmDeliveryView,
    ConfirmReturnView,
    CreateTransferView,
    RejectTransferView,
    RequestReturnView,
    TransferListView,
    dashboard_summary,
    export_transfers_csv,
)

urlpatterns = [
    path('create/', CreateTransferView.as_view()),
    path('list/', TransferListView.as_view()),
    path('summary/', dashboard_summary),
    path('export/', export_transfers_csv),
    path('approve/<int:pk>/', ApproveTransferView.as_view()),
    path('reject/<int:pk>/', RejectTransferView.as_view()),
    path('cancel/<int:pk>/', CancelTransferView.as_view()),
    path('confirm/<int:pk>/', ConfirmDeliveryView.as_view()),
    path('return/<int:pk>/', RequestReturnView.as_view()),
    path('approve-return/<int:pk>/', ConfirmReturnView.as_view()),
]
