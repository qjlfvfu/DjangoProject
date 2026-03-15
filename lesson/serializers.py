from rest_framework import serializers
from .models import Course, Lesson


class LessonListSerializer(serializers.ModelSerializer):
    """
    КОМПАКТНЫЙ сериализатор для урока
    (используется внутри сериализатора курса и для списка уроков)
    """
    class Meta:
        model = Lesson
        fields = ['id', 'name', 'preview', 'course']


class LessonDetailSerializer(serializers.ModelSerializer):
    """
    ПОЛНЫЙ сериализатор для урока
    (используется для создания, обновления и детального просмотра)
    """
    course_name = serializers.CharField(source='course.name', read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)

    class Meta:
        model = Lesson
        fields = [
            'id', 'name', 'description', 'preview', 'video_link',
            'course', 'course_name', 'owner', 'owner_email'
        ]
        read_only_fields = ['owner']


class CourseSerializer(serializers.ModelSerializer):
    """
    Сериализатор для курса с компактным выводом уроков
    """
    lessons = LessonListSerializer(many=True, read_only=True)
    lessons_count = serializers.IntegerField(source='lessons.count', read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'name', 'preview', 'description',
            'owner', 'owner_email', 'lessons_count', 'lessons'
        ]
        read_only_fields = ['owner']