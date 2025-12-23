from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Count, Max
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import ChatRoom, Message, UserProfile, Notification
from .forms import ChatRoomForm, MessageForm, UserProfileForm
import json

@login_required
def index(request):
    """
    Home page - shows all chat rooms and recent conversations
    """
    # Get all rooms the user is part of
    rooms = ChatRoom.objects.filter(
        Q(creator=request.user) | Q(participants=request.user)
    ).distinct().order_by('-updated_at')
    
    # Get recent messages for preview
    recent_messages = {}
    for room in rooms:
        last_message = room.messages.order_by('-timestamp').first()
        if last_message:
            recent_messages[room.id] = last_message
    
    # Get online users
    online_users = UserProfile.objects.filter(
        online_status=True
    ).exclude(user=request.user).select_related('user')
    
    context = {
        'rooms': rooms,
        'recent_messages': recent_messages,
        'online_users': online_users,
        'user_profile': request.user.profile if hasattr(request.user, 'profile') else None,
    }
    
    return render(request, 'chat/index.html', context)

@login_required
def room_detail(request, room_id):
    """
    Chat room detail view
    """
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Check if user has access to the room
    if room.is_private and request.user not in room.participants.all() and request.user != room.creator:
        return redirect('chat:index')
    
    messages = room.messages.all().order_by('timestamp')
    
    # Mark notifications as read
    Notification.objects.filter(
        user=request.user,
        message__room=room,
        is_read=False
    ).update(is_read=True)
    
    context = {
        'room': room,
        'messages': messages,
        'user_profile': request.user.profile if hasattr(request.user, 'profile') else None,
    }
    
    return render(request, 'chat/room.html', context)

@login_required
def create_room(request):
    """
    Create a new chat room
    """
    if request.method == 'POST':
        form = ChatRoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.creator = request.user
            room.save()
            form.save_m2m()  # Save participants
            
            # Add creator as participant
            room.participants.add(request.user)
            
            return redirect('chat:room_detail', room_id=room.id)
    else:
        form = ChatRoomForm()
    
    context = {
        'form': form,
        'title': _('Create New Chat Room'),
    }
    
    return render(request, 'chat/room_form.html', context)

@login_required
@require_POST
def send_message(request, room_id):
    """
    API endpoint to send a message
    """
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Check if user has access to the room
    if request.user not in room.participants.all() and request.user != room.creator:
        return JsonResponse({'error': _('Access denied')}, status=403)
    
    data = json.loads(request.body)
    content = data.get('content', '').strip()
    
    if not content:
        return JsonResponse({'error': _('Message cannot be empty')}, status=400)
    
    # Create message
    message = Message.objects.create(
        room=room,
        sender=request.user,
        content=content
    )
    
    # Create notifications for other participants
    participants = room.participants.exclude(id=request.user.id)
    for participant in participants:
        Notification.objects.create(
            user=participant,
            message=message
        )
    
    # Update room's updated_at
    room.save()
    
    return JsonResponse({
        'success': True,
        'message_id': str(message.id),
        'timestamp': message.timestamp.isoformat(),
    })

@login_required
def user_profile(request, username):
    """
    User profile view
    """
    user = get_object_or_404(User, username=username)
    user_profile = get_object_or_404(UserProfile, user=user)
    
    context = {
        'profile_user': user,
        'user_profile': user_profile,
    }
    
    return render(request, 'chat/profile.html', context)

@login_required
def edit_profile(request):
    """
    Edit user profile
    """
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            
            # Update language preference in session
            request.session['django_language'] = form.cleaned_data['language']
            
            return redirect('chat:user_profile', username=request.user.username)
    else:
        form = UserProfileForm(instance=profile)
    
    context = {
        'form': form,
        'title': _('Edit Profile'),
    }
    
    return render(request, 'chat/profile_form.html', context)

@login_required
def notifications(request):
    """
    User notifications
    """
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:50]
    
    context = {
        'notifications': notifications,
    }
    
    return render(request, 'chat/notifications.html', context)

@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """
    Mark notification as read
    """
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    
    notification.is_read = True
    notification.save()
    
    return JsonResponse({'success': True})

# API Views
@login_required
def get_online_users(request):
    """
    API endpoint to get online users
    """
    online_users = UserProfile.objects.filter(
        online_status=True
    ).exclude(user=request.user).select_related('user')
    
    users_data = [
        {
            'id': profile.user.id,
            'username': profile.user.username,
            'avatar_url': profile.avatar.url if profile.avatar else None,
            'last_seen': profile.last_seen.isoformat() if profile.last_seen else None,
        }
        for profile in online_users
    ]
    
    return JsonResponse({'online_users': users_data})

@login_required
def search_users(request):
    """
    API endpoint to search for users
    """
    query = request.GET.get('q', '')
    
    if not query or len(query) < 2:
        return JsonResponse({'users': []})
    
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    ).exclude(id=request.user.id)[:10]
    
    users_data = [
        {
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name(),
        }
        for user in users
    ]
    
    return JsonResponse({'users': users_data})