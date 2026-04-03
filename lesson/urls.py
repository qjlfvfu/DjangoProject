from django.urls import path, include
from rest_framework import views
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet,
    LessonCreateAPIView,
    LessonDestroyAPIView,
    LessonListAPIView,
    LessonRetrieveAPIView,
    LessonUpdateAPIView,
    CheckoutSessionStatusView,
    CreateCheckoutSessionView,
)

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="course")

app_name = "lesson"

urlpatterns = [
    path("", include(router.urls)),
    path("lessons/create/", LessonCreateAPIView.as_view(), name="lesson-create"),
    path("lessons/list/", LessonListAPIView.as_view(), name="lesson-list"),
    path("lessons/<int:pk>/", LessonRetrieveAPIView.as_view(), name="lesson-retrieve"),
    path(
        "lessons/update/<int:pk>/", LessonUpdateAPIView.as_view(), name="lesson-update"
    ),
    path(
        "lessons/delete/<int:pk>/", LessonDestroyAPIView.as_view(), name="lesson-delete"
    ),
    path('checkout/<int:course_id>/', CreateCheckoutSessionView.as_view(), name='checkout'),
    path('checkout-status/<str:session_id>/', CheckoutSessionStatusView.as_view(), name='checkout-status'),
]
