from django.urls import path, include
from rest_framework.routers import DefaultRouter

from catalog.urls import app_name
from .views import CourseViewSet, LessonCreateAPIView, LessonDestroyAPIView, LessonListAPIView, LessonRetrieveAPIView, \
    LessonUpdateAPIView

# Создаем роутер
router = DefaultRouter()

# Регистрируем ViewSet'ы
router.register(r'courses', CourseViewSet, basename='course')

app_name="lesson"

# Подключаем маршруты
urlpatterns = [
    path('lessons/create/', LessonCreateAPIView.as_view(),name='lesson-create'),
    path('lessons/list/', LessonListAPIView.as_view(),name='lesson-list'),
    path('lessons/<int:pk>/', LessonRetrieveAPIView.as_view(),name='lesson-retrieve'),
    path('lessons/update/<int:pk>/', LessonUpdateAPIView.as_view(),name='lesson-update'),
    path('lessons/delete/<int:pk>/', LessonDestroyAPIView.as_view(),name='lesson-delete'),
]