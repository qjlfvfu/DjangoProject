from rest_framework import serializers
from .models import Course, Lesson, Subscription
from .validators import validate_youtube_url, YouTubeURLValidator


class LessonListSerializer(serializers.ModelSerializer):
    """
    КОМПАКТНЫЙ сериализатор для урока
    (используется внутри сериализатора курса и для списка уроков)
    """

    class Meta:
        model = Lesson
        fields = ["id", "name", "preview", "course"]


class LessonDetailSerializer(serializers.ModelSerializer):
    """
    ПОЛНЫЙ сериализатор для урока
    (используется для создания, обновления и детального просмотра)
    """

    course_name = serializers.CharField(source="course.name", read_only=True)
    owner_email = serializers.EmailField(source="owner.email", read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id",
            "name",
            "description",
            "preview",
            "video_url",
            "video_link",
            "course",
            "course_name",
            "owner",
            "owner_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["owner", "created_at", "updated_at"]
        validators = [YouTubeURLValidator(field="video_url")]


class CourseSerializer(serializers.ModelSerializer):
    """
    Сериализатор для курса с компактным выводом уроков и признаком подписки
    """

    lessons = LessonListSerializer(many=True, read_only=True)
    lessons_count = serializers.IntegerField(source="lessons.count", read_only=True)
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "preview",
            "description",
            "price",
            "owner",
            "owner_email",
            "lessons_count",
            "lessons",
            "is_subscribed",
        ]
        read_only_fields = ["owner"]

    def get_is_subscribed(self, obj):
        """
        Проверяет, подписан ли текущий пользователь на курс
        """
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(user=request.user, course=obj).exists()
        return False


