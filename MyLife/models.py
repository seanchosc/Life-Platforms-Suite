from django.db import models

# Create your models here.

# File: models.py
# Author: Si Yeon Cho (seancho@bu.edu)
# Description: defines the models for my app

# Import built in django User model #
from django.contrib.auth.models import User

# Import Coalesce to sort event times by start and end time
from django.db.models.functions import Coalesce

#Import datetime
from datetime import datetime, date, timedelta
from django.utils import timezone

# Profile model # 
class Profile(models.Model):
    '''Encapsulate the idea of a Profile.'''

    # Profile attributes
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='project_profile')
    first_name = models.TextField()
    last_name = models.TextField()
    email_address = models.TextField(blank=False) # person's email attribute
    profile_photo = models.ImageField(blank=True)
    timezone = models.CharField(max_length=10)

    # override str function
    def __str__(self):
        '''Return a string representation of this Profile object.'''
        return f'{self.first_name} {self.last_name}' # return as string their full name (no middle name attribute)
    # custom get name function
    def get_name(self):
        ''' Returns the first and last name of a given Profile'''
        return f"{self.first_name} {self.last_name}"
    def add_collaborator(self, other, collaborator_type):
        # edge case check
        if other == self:
            return "Error: Can't collaborate with yourself."
        
        # reference the profiles
        profile1 = self.profile 
        profile2 = other.profile
        collaborator1 = Collaborator.objects.filter(inviter=profile1, invitee=profile2, collaborator_type=collaborator_type)
        collaborator2 = Collaborator.objects.filter(inviter=profile2, invitee=profile1, collaborator_type=collaborator_type)

        # edge case
        if collaborator1.exists() or collaborator2.exists():
            return "Error: Already collaborators or pending request exists."
        # Otherwise, create collaborator relationship
        Collaborator.objects.create(inviter=profile1,invitee=profile2,collaborator_type=collaborator_type,invite_status='pending')

        return "Collaborator request sent!"
    
    # custom function to accept a collaborator request
    def accept_collaborator(self, other, collaborator_type):
        ''' Returns confirmation of whether or not a collaborator request was accepted'''

        profile1 = other.profile
        profile2 = self.profile

        # find all pending invites
        pending_invites = Collaborator.objects.filter(inviter=profile1, invitee=profile2, collaborator_type=collaborator_type, invite_status='pending')

        # if any pending invites for the profile exists, accept
        if pending_invites.exists():
            collaborator = pending_invites.first()
            collaborator.invite_status = 'accepted'
            collaborator.save()
            return "Collaborator request accepted."
        # else, no pending collaborator invites
        else:
            return "No pending collaborator request."
        
    # custom function to add a collaborator to an event
    def add_event_collaborator(self, event, other, role='attendee'):
        """Send an event invitation to another user (friend/work contact)"""

        profile1 = self
        profile2 = other

        # edge case, cant friend yourself
        if profile1 == profile2:
            return "Error: Can't invite yourself to an event."

        # Prevent duplicates
        existing_invite = EventInvite.objects.filter(event=event, invitee=profile2)
        existing_collab = EventCollaborator.objects.filter(event=event, collaborator=profile2)

        # if an event invite was already sent to the invitee, return error message
        if existing_invite.exists():
            return "Invite already sent for this event."
        # if a collaborator invite was already sent to the invitee, return error message
        if existing_collab.exists():
            return "User is already a collaborator for this event."

        # Send the invite
        EventInvite.objects.create(event=event, inviter=profile1, invitee=profile2, invite_status='pending')
        return "Event invite sent!"

    # custom function to accept an invite to an event
    def accept_event_collaborator(self, event):
        """Accept an invitation to an event and become a collaborator"""
        profile = self

        # find all pending invites
        pending_invite = EventInvite.objects.filter(event=event, invitee=profile, invite_status='pending')

        # if any pending invites for the profile exists, accept
        if pending_invite.exists():
            invite = pending_invite.first()
            invite.invite_status = 'accepted'
            invite.save()

            EventCollaborator.objects.create(event=event, collaborator=profile, role='attendee')
            return "Event invite accepted!"
        # else, there are no pending invites
        else:
            return "No pending invite."

# Event Query Set #
class EventQuerySet(models.QuerySet):

    # function to order events based on time for edge cases like when event_start_time is given but not end time
    def ordered_by_event_time(self):
        return self.annotate(event_time=Coalesce('event_start_time', 'event_end_time')).order_by('event_date', 'event_time')
    
# Event Model # 
class Event(models.Model):
    ''' encapsulates the idea of an Event'''

    EVENT_TYPES = [('self', 'Self'), ('friends', 'Friends'), ('work', 'Work')] # Types of events
    event_title = models.CharField(max_length=60) # Event title
    event_description = models.TextField(blank=True) # Event description, text field because we will allow long event descriptions
    event_start_time = models.TimeField(null = True, blank = True) # Event start time, optional
    event_end_time = models.TimeField(null = True, blank= True) # Event end time, optional
    event_date = models.DateField() # Event date, this is required
    event_creator = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='created_events') # Creator of the event
    event_type = models.CharField(max_length=7, choices=EVENT_TYPES) # type of event

    objects = EventQuerySet.as_manager() # to use custom event ordering function

    # override the built in str function
    def __str__(self):
        # Returns the string representation of an event depending on which date/time fields were given
        if self.event_start_time and self.event_end_time:
            return f'{self.event_title} ({self.event_start_time}~{self.event_end_time} on {self.event_date})'
        elif self.event_start_time:
            return f'{self.event_title} (Starts at: {self.event_start_time} on {self.event_date})'
        elif self.event_end_time:
            return f'{self.event_title} (Ends at: {self.event_end_time} on {self.event_date})'
        else:
            return f'{self.event_title} on {self.event_date}'
        
    class Meta:
        # Meta class to provide ordering details"
        ordering = ['event_date', 'event_start_time'] # Default sorting behavior, but will use Coalesce when needed 
                                                      # (if event_start_time is given but not end time_)
        
class EventPost(models.Model):
    ''' encapsulates the idea of a post on a specific Event'''

    # The specific event the post is assigned to
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='posts')

    # the author of the post
    post_author = models.ForeignKey(Profile, on_delete=models.CASCADE)

    # the 'caption'/text content assigned to the photo
    post_text_content = models.TextField(blank=True)

    # autogenerated timestamp of the post
    timestamp = models.DateTimeField(auto_now_add=True)

    # override the custom str function
    def __str__(self):
        return f'Post by: {self.post_author.get_name()}, at {self.timestamp}'
    

class EventPostMedia(models.Model):
    ''' class for the media contents of an EventPost'''
    
    # The specific event post that this media content is assigned to
    post = models.ForeignKey(EventPost, on_delete=models.CASCADE, related_name='media')

    # The actual media file/content
    post_media = models.ImageField()

    # override the custom str function
    def __str__(self):
        return f"Media Content for Post {self.post.id} by {self.post.post_author.get_name()}"

class Collaborator(models.Model):
    ''' encapsulates the idea of a collaborator '''
    
    # The possible types of a collaborator (Can change upon more sophisticated development of my project)
    COLLABORATOR_TYPES = [('friend', 'Friend'), ('work', 'Work')]

    # The possible  statuses of an invitation
    INVITE_STATUSES = [('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')]

    # the given inviter
    inviter = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='sent_collaborator_invites')
    # the given invitee
    invitee = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='received_collaborator_invites')

    # the current status of the invitiation
    invite_status = models.CharField(max_length=8, choices=INVITE_STATUSES, default='pending')

    # The assigned type of the collaborator based on the possible collaborator types
    collaborator_type = models.CharField(max_length=6, choices=COLLABORATOR_TYPES)

    # override the custom str function
    def __str__(self):
        inviter_name = self.inviter.get_name()
        invitee_name = self.invitee.get_name()
        if self.invite_status == 'pending':
            return f"{inviter_name}'s collaboration invite to {invitee_name} of type [{self.collaborator_type}] is PENDING"
        elif self.invite_status == 'accepted':
            return f"{inviter_name}'s collaboration invite to {invitee_name} of type [{self.collaborator_type}] is ACCEPTED"
        else:
            return f"{inviter_name}'s collaboration invite to {invitee_name} of type [{self.collaborator_type}] is REJECTED"

class EventInvite(models.Model):
    ''' encapsulates the idea of an invitation to an event'''

    # The possible statuses of an invitiation
    INVITE_STATUSES = [('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')]

    # The given event
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='invites')

    # The given event inviter
    inviter = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='sent_event_invites') 

    # The given event invitee
    invitee = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='received_event_invites')

    # The current status of the invitation
    invite_status = models.CharField(max_length=10, choices=INVITE_STATUSES, default='pending')

    # override the custom str function
    def __str__(self):
        return f"{self.inviter.get_name()} invited {self.invitee.get_name()} to '{self.event.event_title}' [{self.invite_status}]"
class EventCollaborator(models.Model):
    ''' encapsulates the idea of a Collaborator for an Event'''

    # The possible roles that can be assigned for a given collaborator on an event
    ROLE_TYPES = [('attendee', 'Attendee'),('editor', 'Editor')]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='collaborators') # The given event
    collaborator = models.ForeignKey(Profile, on_delete=models.CASCADE)                      # THe given collaborator
    role = models.CharField(max_length=10, choices=ROLE_TYPES, default='attendee')           # The assigned role of the collaborator on an event

    # override the custom str function
    def __str__(self):
        return f"{self.collaborator.get_name()} ({self.role}) is attending event: {self.event.event_title}"

class WorkLog(models.Model):
    # Encapsulates the idea of a Work Log Calendar"
    CATEGORY_CHOICES = [
        ('DEV', 'Development/Coding'),
        ('BIZ', 'Business/Admin'),
        ('LRN', "Learning/Research"),
        ('DES', "Design/UI"),
    ]
    date = models.DateField(default=timezone.now) # Set date for logged event
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)    
    duration = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True) # set duration of logged event
    category = models.CharField(max_length = 3, choices=CATEGORY_CHOICES) # set category of event
    description = models.TextField() # notes
    log_time = models.DateTimeField(auto_now_add=True) # time logged

    def __str__(self):
        #to string function 
        return f"{self.category} activity on {self.date} for {self.duration} hours, logged at {self.log_time}"

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            log_date = self.date if self.date else date.today()
            start = datetime.combine(log_date, self.start_time)
            end = datetime.combine(log_date, self.end_time)
            if end < start:
                end += timedelta(days=1)
            #calculate duration
            dur = end - start
            self.duration = dur.total_seconds() / 3600
        super().save(*args, **kwargs) # save to db
