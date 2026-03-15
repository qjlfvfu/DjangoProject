from rest_framework import serializers
from .models import Course, Lesson


class LessonDetailSerializer(serializers.ModelSerializer):
    """
    ПОЛНЫЙ сериализатор для урока
    (используется для отдельного вывода урока)
    """
    class Meta:
        model = Lesson
        fields = '__all__'  # все поля


class LessonListSerializer(serializers.ModelSerializer):
    """
    ОГРАНИЧЕННЫЙ сериализатор для урока
    (используется ВНУТРИ сериализатора курса)
    """
    class Meta:
        model = Lesson
        fields = ['id', 'title']


class CourseSerializer(serializers.ModelSerializer):
    """
    Сериализатор курса, который использует
    ОГРАНИЧЕННЫЙ сериализатор для вывода уроков
    """
    lessons = LessonListSerializer(many=True, read_only=True)
    lessons_count = serializers.IntegerField(source='lessons.count', read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'owner', 'created_at', 'lessons_count', 'lessons']