from django.urls import path, include
from rest_framework_nested import routers
from .views import TaskViewSet, TaskCommentViewSet, TaskAttachmentViewSet

router = routers.SimpleRouter()
router.register(r'', TaskViewSet, basename='task')

nested_router = routers.NestedSimpleRouter(router, r'', lookup='task')
nested_router.register(r'comments', TaskCommentViewSet, basename='task-comment')
nested_router.register(r'attachments', TaskAttachmentViewSet, basename='task-attachment')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(nested_router.urls)),
] 