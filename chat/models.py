from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinLengthValidator
import uuid

class ChatRoom(models.Model):
    """
    Model representing a chat room
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name=_('Room Name'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms', verbose_name=_('Creator'))
    participants = models.ManyToManyField(User, related_name='chat_rooms', blank=True, verbose_name=_('Participants'))
    is_private = models.BooleanField(default=False, verbose_name=_('Private Room'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    class Meta:
        verbose_name = _('Chat Room')
        verbose_name_plural = _('Chat Rooms')
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.name
    
    def get_participants_count(self):
        return self.participants.count()
    
    def last_message(self):
        return self.messages.order_by('-timestamp').first()

class Message(models.Model):
    """
    Model representing a chat message
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages', verbose_name=_('Chat Room'))
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', verbose_name=_('Sender'))
    content = models.TextField(validators=[MinLengthValidator(1)], verbose_name=_('Message'))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_('Timestamp'))
    is_read = models.BooleanField(default=False, verbose_name=_('Is Read'))
    parent_message = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies', verbose_name=_('Parent Message'))
    
    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()

class UserProfile(models.Model):
    """
    Extended user profile for chat features
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    online_status = models.BooleanField(default=False, verbose_name=_('Online Status'))
    last_seen = models.DateTimeField(default=timezone.now, verbose_name=_('Last Seen'))
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name=_('Avatar'))
    language = models.CharField(max_length=10, choices=[
        ('en', 'English'),
        ('ar', 'Arabic')
    ], default='en', verbose_name=_('Language'))
    theme = models.CharField(max_length=10, choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto')
    ], default='auto', verbose_name=_('Theme'))
    
    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def update_online_status(self, status):
        self.online_status = status
        if not status:
            self.last_seen = timezone.now()
        self.save()

class Notification(models.Model):
    """
    Model for user notifications
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']