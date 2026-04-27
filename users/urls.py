from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    MyTokenObtainPairView,
    UserListAPIView,
    UserRetrieveAPIView,
    UserCreateAPIView,
    UserUpdateAPIView,
    UserDestroyAPIView,
    PaymentListAPIView,
)

app_name = "users"

urlpatterns = [
    # JWT токены
    path("token/", MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Регистрация (доступна без авторизации)
    path("register/", UserCreateAPIView.as_view(), name="register"),
    # CRUD для пользователей (требуют авторизации)
    path("users/", UserListAPIView.as_view(), name="user-list"),
    path("users/me/", UserRetrieveAPIView.as_view(), {"pk": "me"}, name="user-me"),
    path("users/<int:pk>/", UserRetrieveAPIView.as_view(), name="user-detail"),
    path("users/<int:pk>/update/", UserUpdateAPIView.as_view(), name="user-update"),
    path("users/<int:pk>/delete/", UserDestroyAPIView.as_view(), name="user-delete"),
    # Платежи
    path("payments/", PaymentListAPIView.as_view(), name="payment-list"),
]
