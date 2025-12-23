from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import ChatRoom, Message, UserProfile, Notification

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'get_participants_count', 'is_private', 'created_at')
    list_filter = ('is_private', 'created_at')
    search_fields = ('name', 'description', 'creator__username')
    filter_horizontal = ('participants',)
    
    def get_participants_count(self, obj):
        return obj.participants.count()
    get_participants_count.short_description = _('Participants')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'room', 'content_preview', 'timestamp', 'is_read')
    list_filter = ('timestamp', 'is_read', 'room')
    search_fields = ('content', 'sender__username', 'room__name')
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = _('Content')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'online_status', 'last_seen', 'language', 'theme')
    list_filter = ('online_status', 'language', 'theme')
    search_fields = ('user__username', 'user__email')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message_preview', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    
    def message_preview(self, obj):
        return obj.message.content[:50] + '...' if len(obj.message.content) > 50 else obj.message.content
    message_preview.short_description = _('Message')