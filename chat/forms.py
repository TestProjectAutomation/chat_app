from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import ChatRoom, Message, UserProfile

class ChatRoomForm(forms.ModelForm):
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
        required=False,
        label=_('Participants')
    )
    
    class Meta:
        model = ChatRoom
        fields = ['name', 'description', 'is_private', 'participants']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': _('Enter room name')
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': _('Enter room description (optional)'),
                'rows': 3
            }),
            'is_private': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
            }),
        }
        labels = {
            'name': _('Room Name'),
            'description': _('Description'),
            'is_private': _('Private Room'),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none',
                'placeholder': _('Type your message here...'),
                'rows': 3,
                'id': 'message-input'
            }),
        }
        labels = {
            'content': _('Message'),
        }

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ['avatar', 'language', 'theme', 'first_name', 'last_name', 'email']
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg'
            }),
            'language': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'theme': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        
        # Update user fields
        if self.instance.user:
            self.instance.user.first_name = self.cleaned_data['first_name']
            self.instance.user.last_name = self.cleaned_data['last_name']
            self.instance.user.email = self.cleaned_data['email']
            self.instance.user.save()
        
        if commit:
            profile.save()
        
        return profile