from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet,
    CreateCheckoutForSubscriptionView,
    CreateSubscriptionPriceView,
    CreateSubscriptionPriceWithProductView,
    LessonCreateAPIView,
    LessonDestroyAPIView,
    LessonListAPIView,
    LessonRetrieveAPIView,
    LessonUpdateAPIView,
    CheckoutSessionStatusView,
    CreateCheckoutSessionView,
    CreateStripeProductPriceView,
    DeleteStripeProductView,
    SimpleCheckoutSessionView,
    WebhookStripeView,
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
    path(
        "checkout/<int:course_id>/",
        CreateCheckoutSessionView.as_view(),
        name="checkout",
    ),
    path(
        "checkout-status/<str:session_id>/",
        CheckoutSessionStatusView.as_view(),
        name="checkout-status",
    ),
    # Управление продуктами Stripe
    path(
        "courses/<int:course_id>/stripe/setup/",
        CreateStripeProductPriceView.as_view(),
        name="stripe_setup",
    ),
    path(
        "courses/<int:course_id>/stripe/delete/",
        DeleteStripeProductView.as_view(),
        name="stripe_delete",
    ),
    path(
        "create-checkout/", SimpleCheckoutSessionView.as_view(), name="create_checkout"
    ),
    path(
        "stripe/create-subscription-price/",
        CreateSubscriptionPriceView.as_view(),
        name="create_subscription_price",
    ),
    path(
        "stripe/create-subscription-with-product/",
        CreateSubscriptionPriceWithProductView.as_view(),
        name="create_subscription_with_product",
    ),
    path(
        "stripe/subscription-checkout/",
        CreateCheckoutForSubscriptionView.as_view(),
        name="subscription_checkout",
    ),
    # Вебхук Stripe
    path("stripe/webhook/", WebhookStripeView.as_view(), name="stripe_webhook"),
]
