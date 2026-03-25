from django.urls import path
from .views import TransactionSubmissionView, get_transactions_after, validate_transaction, finalize_transaction

urlpatterns = [
    path("transactions/", get_transactions_after),
    path("submit/", TransactionSubmissionView.as_view()),
    path("validate/", validate_transaction),
    path("finalize-transaction/", finalize_transaction),    
]
