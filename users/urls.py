from django.urls import path
from .views import PaymentListAPIView
from .views import MyTokenObtainPairView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


app_name = 'users'

urlpatterns = [
    path('payments/', PaymentListAPIView.as_view(), name='payment-list'),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('profile/', UserProfileView.as_view(), name='profile'),
    # path('register/', UserRegisterView.as_view(), name='register'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]