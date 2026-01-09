from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Task, TaskComment, TaskAttachment

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name')

class TaskCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TaskComment
        fields = ('id', 'user', 'content', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

class TaskAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = TaskAttachment
        fields = ('id', 'file', 'uploaded_by', 'uploaded_at', 'description')
        read_only_fields = ('uploaded_at',)

class TaskSerializer(serializers.ModelSerializer):
    assigned_to = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    comments = TaskCommentSerializer(many=True, read_only=True)
    attachments = TaskAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = ('id', 'title', 'description', 'status', 'priority',
                 'assigned_to', 'created_by', 'due_date', 'completed_at',
                 'created_at', 'updated_at', 'comments', 'attachments')
        read_only_fields = ('created_at', 'updated_at', 'completed_at')

class TaskCreateSerializer(serializers.ModelSerializer):
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='assigned_to',
        write_only=True
    )

    class Meta:
        model = Task
        fields = ('title', 'description', 'status', 'priority',
                 'assigned_to_id', 'due_date')

class TaskUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('title', 'description', 'status', 'priority',
                 'assigned_to', 'due_date')

class TaskCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskComment
        fields = ('content',)

class TaskAttachmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskAttachment
        fields = ('file', 'description') 