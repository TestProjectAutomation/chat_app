from django.urls import path
from django.utils.translation import gettext_lazy as _
from . import views

app_name = 'chat'

urlpatterns = [
    # path('', views.index, name='index'),
    # path('room/<uuid:room_id>/', views.room_detail, name='room_detail'),
    # path('room/create/', views.create_room, name='create_room'),
    # path('room/<uuid:room_id>/send/', views.send_message, name='send_message'),
    # path('profile/<str:username>/', views.user_profile, name='user_profile'),
    # path('profile/edit/', views.edit_profile, name='edit_profile'),
    # path('notifications/', views.notifications, name='notifications'),
    # path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    # path('api/online-users/', views.get_online_users, name='get_online_users'),
    # path('api/search-users/', views.search_users, name='search_users'),
]