from django.urls import path
from .views import PaymentListAPIView

app_name = 'users'

urlpatterns = [
    path('payments/', PaymentListAPIView.as_view(), name='payment-list'),
    # path('profile/', UserProfileView.as_view(), name='profile'),
    # path('register/', UserRegisterView.as_view(), name='register'),
]