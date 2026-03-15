from rest_framework import serializers
from .models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    lessons = serializers.SerializerMethodField()
    lessons_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'owner', 'created_at', 'lessons_count', 'lessons']

    def get_lessons_count(self, instance):
        """Возвращает количество уроков в курсе"""
        return instance.lessons.count()

    def get_lesson(self,instance):
        """Возвращает все уроки в курсе"""
        lessons=instance.lessons.all()
        return LessonSerializer(lessons,many=True).data