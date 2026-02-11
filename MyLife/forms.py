from django import forms
from .models import * # Import models
from django.forms import inlineformset_factory ## TO ALLOW MULTIPLE MEDIA FILES PER POST

# File: forms.py
# Author: Si Yeon Cho (seancho@bu.edu)
# Description: defines the forms for my app

class CreateProfileForm(forms.ModelForm):
    ''' A form to create a Profile and add it to DB'''
    class Meta:
        '''associate this form with a model from our database.'''
        # use profile model
        model = Profile
        # fields associated with a Profile
        fields = ['first_name', 'last_name', 'email_address', 'profile_photo', 'timezone']

class UpdateProfileForm(forms.ModelForm):
    ''' A form to update a Profile to the database'''
    class Meta:
        ''' associate this form with the Profile model; select fields'''
        # use profile model
        model = Profile

        # fields that you can change
        fields = ['email_address', 'profile_photo', 'timezone']

class EventForm(forms.ModelForm):
    ''' A form to create an event on calendar '''
    class Meta:
        ''' associate this form with the Event model'''
        # use event model
        model = Event

        # fields associated with an Event
        fields = ['event_title', 'event_description', 'event_start_time', 'event_end_time', 'event_date', 'event_type']

class UpdateEventForm(forms.ModelForm):
    ''' A form to update an Event to the database'''
    class Meta:
        ''' associate this form with the Event model'''
        # use event model
        model = Event

        # fields that you can change for an event
        fields = ['event_title', 'event_description', 'event_start_time', 'event_end_time', 'event_date']

class EventPostForm(forms.ModelForm):
    ''' A form to create a post for an Event to the database'''

    class Meta:
        ''' associate this form with the EventPost model'''
        model = EventPost # link this form to the EventPost model
        fields = ['post_text_content'] # plain textarea
        widgets = {
            # render the text field as a 5-line textarea with filler words (Share an update)
            'post_text_content': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Share an update.'
            })
        }
EventPostMediaFormSet = inlineformset_factory(
    parent_model=EventPost, # ties the images to a specific post
    model=EventPostMedia, # the model holding each image
    fields=['post_media'], # the ImageField on EventPostMedia
    extra=5, # maximum of five files per media post
    widgets={'post_media': forms.ClearableFileInput()},
    can_delete =False # Weird delete checkboxes were there so false
    )

### INVITES ####

# form to choose the type of collaborator (friend or work)
class CollaboratorInviteForm(forms.Form):
    collaborator_type = forms.ChoiceField(choices=Collaborator.COLLABORATOR_TYPES) # the collaborator types defined in my models

# form to pick which Profile to invite to an event
class EventInviteForm(forms.Form):              # filled in view
    invitee_id = forms.ModelChoiceField(queryset=Profile.objects.none(), label="Who do you want to invite?")
    