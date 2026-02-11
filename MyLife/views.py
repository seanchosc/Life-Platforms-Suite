# Imports
from django.shortcuts import render, redirect
from django.views.generic import *
from .models import *
from .forms import *
from django.urls import reverse, reverse_lazy

from django.contrib.auth.mixins import LoginRequiredMixin ## for requiring user to be logged in
from django.views.generic import TemplateView # For logout confirmation redirect page
from django.contrib.auth.forms import UserCreationForm ## 
from django.contrib.auth.models import User ## 
from django.contrib.auth import login # 
from django.views.generic.base import ContextMixin, View

from datetime import datetime, time  # new
from django.views.generic import TemplateView, View   # new
from django.http import HttpResponseForbidden, JsonResponse  # new

from django.contrib import messages 

# File: views.py
# Author: Si Yeon Cho (seancho@bu.edu)
# Description: defines the views that my project will use

# Create your views here.
# BASE VIEW
class BaseView(TemplateView):
    template_name = 'MyLife/base.html' # use base template
    def get_context_data(self, **kwargs):
        '''Return the dictionary of context variables for use in the template.'''
        # get the default context
        context = super().get_context_data(**kwargs)
        # if the user is logged in, add their Profile object
        user = self.request.user
        if user.is_authenticated:
            # check whether the user already has a profile
            has_profile = Profile.objects.filter(user=user).exists()
            context['has_profile'] = has_profile  # for nav logic
            # only fetch and inject the profile if it truly exists
            if has_profile:
                context['profile'] = Profile.objects.get(user=user)
        return context
    
class HomeView(TemplateView):
    template_name = 'MyLife/home.html'

    def get_context_data(self, **kwargs):
        '''Return the dictionary of context variables for use in the template.'''
        context = super().get_context_data(**kwargs) # default context
        user = self.request.user
        context['has_profile'] = (
            user.is_authenticated
            and Profile.objects.filter(user=user).exists()
        )
        return context
class ShowUserDashboardView(TemplateView):
    '''Show a user's dashboard'''
    model = Profile # retrieve objects of type Profile from the database
    template_name = 'MyLife/user_dashboard.html' # Use the user dashboard template
    context_object_name = 'profile' # how to find the data in the template file
    
    def get_object(self, queryset=None):
    # always fetch the profile for the logged-in user
        return Profile.objects.get(user=self.request.user)
    def get_context_data(self, **kwargs):
        '''Return the dictionary of context variables for use in the template.'''
        context = super().get_context_data(**kwargs) # call superclass

        # try to fetch the logged-in user’s profile
        try:
            profile = Profile.objects.get(user=self.request.user)
            has_profile = True
        except Profile.DoesNotExist:
            profile = None
            has_profile = False

        context['has_profile'] = has_profile
        context['profile']= profile

        if has_profile:
            # === your original DetailView logic, verbatim ===

            # Events created by the user
            created_events = Event.objects.filter(event_creator=profile)
            # Events where the user is a collaborator
            event_collaborator = EventCollaborator.objects.filter(collaborator=profile)
            events = [ec.event for ec in event_collaborator]
            # Combine
            all_events = list(created_events) + events

            # Pending event invites
            pending_event_invites_received = EventInvite.objects.filter(
                invitee=profile, invite_status='pending')
            pending_event_invites_sent = EventInvite.objects.filter(
                inviter=profile, invite_status='pending')

            # Accepted collaborators
            sent_accepted = Collaborator.objects.filter(
                inviter=profile, invite_status='accepted')
            received_accepted = Collaborator.objects.filter(
                invitee=profile, invite_status='accepted')
            accepted_collaborators = list(sent_accepted) + list(received_accepted)
            # Pending collaborators
            pending_collab_invites_sent = Collaborator.objects.filter(
                inviter=profile, invite_status='pending')
            # Pending invites received
            pending_collab_invites_received = Collaborator.objects.filter(
                invitee=profile, invite_status='pending')

            context['events'] = all_events
            context['pending_event_invites_received'] = pending_event_invites_received
            context['pending_event_invites_sent'] = pending_event_invites_sent
            context['collaborators']= accepted_collaborators
            context['pending_collab_invites_sent']= pending_collab_invites_sent
            context['pending_collab_invites_received']= pending_collab_invites_received

            # === end of your old code ===

        return context
    
### Create Profile View ###

class CreateProfileView(LoginRequiredMixin, CreateView):
    '''A view to handle creation of a new Profile.
    (1) display the HTML form to user (GET)
    (2) process the form submission and store the new Profile object (POST)
    '''
    form_class = CreateProfileForm # use the CreateProfileForm class in forms
    template_name = 'MyLife/create_profile_form.html' # show create_profile_form template
    context_object_name = 'form' # how to find the data in the template file

    def get_login_url(self) -> str:
        '''return the URL required for login'''
        return reverse('login')

    def form_valid(self, form):
        '''
        Handle the form submission to create a new Profile object.
        '''
        # attach the current user to the profile instance
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        '''Return the dictionary of context variables for use in the template.'''
        # calling the superclass method
        context = super().get_context_data(**kwargs)
        # add this form into the context dictionary when needed
        if (not self.request.user.is_authenticated 
            or Profile.objects.filter(user=self.request.user).exists()):
            context['create_user_form'] = UserCreationForm()
        return context
    def get_success_url(self):
        return reverse('user_dashboard')
### Update Profile View ###
class UpdateProfileView(LoginRequiredMixin, UpdateView):
    ''' A view to handle updating an existing Profile'''
    model = Profile
    form_class = UpdateProfileForm
    template_name ='MyLife/update_profile_form.html'

    def get_login_url(self) -> str:
        return reverse('login')

    def get_object(self):
        '''Return the Profile belonging to the logged-in user'''
        return Profile.objects.get(user=self.request.user)

    def form_valid(self, form):
        ''' save updated Profile'''
        print(f'UpdateProfileView: form.cleaned_data={form.cleaned_data}')
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('show_profile') 

class CollaboratorContextMixin:
    """Adds `collaborators` to the context, annotated with a `rel_type` key."""

    def _get_collaborators_for(self, profile):
        '''
        Return a list of dicts:
        Only accepted relationships are included.
        '''
        # Outgoing
        sent = Collaborator.objects.filter(
            inviter=profile, invite_status="accepted"
        ).select_related("invitee")

        # Incoming
        received = Collaborator.objects.filter(
            invitee=profile, invite_status="accepted"
        ).select_related("inviter")

        normalized = [
            {"profile": coll.invitee, "rel_type": "inviter"} for coll in sent
        ] + [
            {"profile": coll.inviter, "rel_type": "invitee"} for coll in received
        ]
        return normalized

    def get_context_data(self, **kwargs):
        '''Return the dictionary of context variables for use in the template.'''
        context = super().get_context_data(**kwargs)
        profile = self.get_object()
        context["collaborators"] = self._get_collaborators_for(profile)
        return context

### Show DetailView to show one Profile:
# MyLife/views.py
#SHOW PROFILE PAGE VIEW:
class ShowProfilePageView(CollaboratorContextMixin, DetailView):
    '''Show the details for one profile.'''
    model = Profile # retrieve objects of type Profile from the database
    template_name = 'MyLife/show_profile.html' # show_profile_page template
    context_object_name = 'profile' # how to find the data in the template file
    def get_object(self, queryset=None):
        pk = self.kwargs.get("pk") # the key
        # pick self profile or other profile
        if pk is not None:
            return Profile.objects.get(pk=pk)
        # default: my own profile
        return Profile.objects.get(user=self.request.user)
    def dispatch(self, request, *args, **kwargs):
        '''redirect to create if no Profile exists yet'''
        if not Profile.objects.filter(user=request.user).exists():
            return redirect('create_profile')
        return super().dispatch(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        '''Return the dictionary of context variables for use in the template.'''

        context = super().get_context_data(**kwargs)
        profile = self.get_object()

        created = Event.objects.filter(event_creator=profile)
        collab   = EventCollaborator.objects.filter(collaborator=profile)
        events   = list(created) + [c.event for c in collab]

        # combine & deduplicate 
        context["events"] = events
        # nav-bar helper
        context["has_profile"] = True
        sent_accepted = Collaborator.objects.filter(
            inviter=profile, invite_status='accepted')
        received_accepted = Collaborator.objects.filter(
            invitee=profile, invite_status='accepted')

        context['collaborators'] = list(sent_accepted) + list(received_accepted)
        return context
class CreateEventView(LoginRequiredMixin, CreateView):
    ''' view for creating an event '''
    form_class = EventForm
    template_name = 'MyLife/create_event_form.html'

    def get_login_url(self) -> str:
        return reverse('login')

    def form_valid(self, form):
        '''Attach the logged-in user’s Profile as creator, then save'''
        print(f'CreateEventView: form.cleaned_data={form.cleaned_data}')
        form.instance.event_creator = Profile.objects.get(user=self.request.user)
        return super().form_valid(form)
    def get_success_url(self):
        return reverse('event_details', kwargs={'pk': self.object.pk})

### Update Event View ###
class UpdateEventView(LoginRequiredMixin, UpdateView):
    ''' A view to handle updating an existing Event.'''
    model = Event
    form_class = UpdateEventForm
    template_name = 'MyLife/update_event_form.html'

    def get_login_url(self) -> str:
        return reverse('login')

    def get_queryset(self):
        '''Only allow editing of Events this user created'''
        return Event.objects.filter(event_creator__user=self.request.user)

    def form_valid(self, form):
        '''save updated Event'''
        print(f'UpdateEventView: form.cleaned_data={form.cleaned_data}')
        return super().form_valid(form)
    
    def get_success_url(self):
        # after editing, go back to the event’s detail page
        return reverse("event_details", kwargs={"pk": self.object.pk})

class LogoutRedirectView(TemplateView):
    ''' View for being redirected to logout confirmation page'''
    template_name = 'MyLife/logged_out.html' ## show the logged_out template 

from django.contrib.auth.views import LogoutView

class CustomLogoutView(LogoutView):
    """ Allows GET on logout """

    # override http_method_names
    http_method_names = ['get', 'post']
    def get(self, request, *args, **kwargs):
        # treat GET exactly like POST
        print("CustomLogoutView GET called")      
        return self.post(request, *args, **kwargs)
class UserRegistrationView(CreateView):
    '''A view to show/process the registration form to create a new User.'''
    template_name = 'MyLife/register.html' # show the register template
    form_class = UserCreationForm # use the imported UserCreationForm class

    def form_valid(self, form):
        # 1) save the new user
        user = form.save()
        # 2) log them in
        login(self.request, user)
        # 3) send them to the dashboard instead of create_profile
        return redirect('user_dashboard')
    
class ShowEventDetailsView(LoginRequiredMixin, DetailView):
    '''Display the full details for a single Event object.'''
    model = Event
    template_name = 'MyLife/show_event_details.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        '''Return the dictionary of context variables for use in the template.'''

        context = super().get_context_data(**kwargs)
        event = self.get_object()

        # accepted collaborators
        context['collaborators']= event.collaborators.all()

        # pending invites for this event
        context['pending_invites'] = (EventInvite.objects.filter(event=event, invite_status='pending'))

                # newest first
        context['posts'] = event.posts.select_related('post_author').prefetch_related('media').order_by("timestamp")
        # helper flag for the template
        profile = self.request.user.project_profile
        context['can_post'] = (profile == event.event_creator or event.collaborators.filter(collaborator=profile).exists())
        context["can_invite"] = (profile == event.event_creator or event.collaborators.filter(collaborator=profile, role__in=["attendee","editor"]).exists()
        )
        return context
class CreateEventPostView(LoginRequiredMixin, CreateView):
    '''
    handles the form & inline media in one go
    URL: /MyLife/events/<event_pk>/posts/new/
    '''
    model = EventPost
    form_class = EventPostForm
    template_name = "MyLife/create_event_post_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.event = Event.objects.get(pk=self.kwargs["event_pk"])
        profile = request.user.project_profile  # you already have this prop
        allowed = (profile == self.event.event_creator or self.event.collaborators.filter(collaborator=profile).exists())
        if not allowed:
            return HttpResponseForbidden("Not allowed")
        return super().dispatch(request, *args, **kwargs)

    # pass the extra formset to the template
    def get_context_data(self, **kwargs):
        '''Return the dictionary of context variables for use in the template.'''
        context = super().get_context_data(**kwargs) # default context
        context["event"] = self.event
        context["media_formset"] = kwargs.get("media_formset",EventPostMediaFormSet())

        posts = (
            EventPost.objects
            .filter(event=self.object)
            .select_related('post_author')
            .prefetch_related('media')# use the related name
            .order_by('timestamp')
        )
        context['posts'] = posts
        return context
    

    def form_valid(self, form):
        form.instance.event = self.event
        form.instance.post_author = self.request.user.project_profile
        # we need the object before saving the formset
        response = super().form_valid(form)

        media_formset = EventPostMediaFormSet(
            self.request.POST,
            self.request.FILES,
            instance=self.object
        )
        if media_formset.is_valid():
            media_formset.save()
        else: # rollback the post if media invalid
            self.object.delete()
            return self.form_invalid(form)

        messages.success(self.request, "Post added!")
        return response

    def get_success_url(self):
        return reverse("event_details", args=[self.event.pk])

### CALENDAR IMPLEMENTATION ###

class CalendarView(LoginRequiredMixin, TemplateView):
    '''
    show the calendar page using fullcalendar js
    it will load the calendar ui and then call events_json for data
    '''
    template_name = "MyLife/calendar.html"

    # fetch events from events_json
    def events_json(request):
        # get the profile for the current user
        profile = request.user.project_profile
        # grab events created by user
        created = Event.objects.filter(event_creator=profile)
        # grab events where user is a collaborator
        collab = EventCollaborator.objects.filter(collaborator=profile)
        # combine both lists
        events = list(created) + [c.event for c in collab]
        data = []
        for ev in events:
            data.append({
                "id":    ev.pk,
                "title": ev.event_title,
                "start": ev.event_date.isoformat(), # fullcalendar needs iso string
                "url": reverse("event_details", args=[ev.pk]),# link back to event page
            })
        return JsonResponse(data, safe=False)

    def get_context_data(self, **kwargs):
        '''Return the dictionary of context variables for use in the template.'''

        context = super().get_context_data(**kwargs) # default context by calling superclass
        # link back to user dashboard
        context["dashboard_url"] = reverse_lazy("user_dashboard")
        user = self.request.user
        # flag if user has a profile
        context["has_profile"] = (
            user.is_authenticated
            and Profile.objects.filter(user=user).exists()
        )
        # get all events sorted by date and time
        events = Event.objects.ordered_by_event_time()
        context["events"] = events

        return context

class EventJsonFeedView(LoginRequiredMixin, View):
    '''
    give a json feed of events for fullcalendar
    returns a list of {title,start,end,id,url}
    '''
    def get(self, request, *args, **kwargs):
        profile = request.user.project_profile

        # grab both created and collaborator events
        created = Event.objects.filter(event_creator=profile)
        collab_qs = EventCollaborator.objects.filter(collaborator=profile)
        events = list(created) + [c.event for c in collab_qs]

        data = []
        for ev in events:
            start = datetime.combine(ev.event_date, ev.event_start_time or time.min)
            end   = datetime.combine(ev.event_date, ev.event_end_time or time.max)
            data.append({
                "id":    ev.pk,
                "title": ev.event_title,
                "start": start.isoformat(),
                "end":   end.isoformat(),
                "url":   reverse("event_details", args=[ev.pk]),
            })
        return JsonResponse(data, safe=False)

def send_collab_invite(request, pk):
    ''' allow a user to invite someone as a collaborator '''
    try:
        target = Profile.objects.get(pk=pk)
    except Profile.DoesNotExist:
        messages.error(request, "No such profile.")
        return redirect("show_profile")

    if request.method == "POST":
        form = CollaboratorInviteForm(request.POST)
        if form.is_valid():
            # send invite from current user to target
            result = request.user.project_profile.add_collaborator(target.user, form.cleaned_data["collaborator_type"])
            messages.success(request, result)
            return redirect("show_person", pk=target.pk)
    else:
        form = CollaboratorInviteForm()

    return render(request, "MyLife/collab_invite_form.html",
                  {"form": form, "target": target})

def respond_collab_invite(request, cid, decision):
    """ let invitee accept or reject a collaborator invite """
    try:
        invite = Collaborator.objects.get(pk=cid)
    except Collaborator.DoesNotExist:
        messages.error(request, "Invite not found.")
        return redirect("show_profile")

    if invite.invitee != request.user.project_profile:
        messages.error(request, "That invite isn’t for you.")
        return redirect("show_profile")

    if decision == "accept":
        invite.invite_status = "accepted"
        invite.save()
        messages.success(request, "Collaborator request accepted.")
    elif decision == "reject":
        invite.invite_status = "rejected"
        invite.save()
        messages.success(request, "Collaborator request rejected.")
    return redirect("show_profile")

def send_event_invite(request, event_id):
    """ let event creator invite a collaborator to the event """
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        messages.error(request, "Event not found.")
        return redirect("calendar")

    if event.event_creator != request.user.project_profile:
        messages.error(request, "Only the creator can invite.")
        return redirect("event_details", pk=event.pk)

    form = EventInviteForm(request.POST or None)
    # only show people who are already accepted collaborators
    accepted = Collaborator.objects.filter(
        inviter=request.user.project_profile, invite_status="accepted"
    ).values_list("invitee", flat=True)
    form.fields["invitee_id"].queryset = Profile.objects.filter(pk__in=accepted)

    if request.method == "POST" and form.is_valid():
        invitee = form.cleaned_data["invitee_id"]
        # send the event invite
        msg = request.user.project_profile.add_event_collaborator(
            event, invitee.user
        )
        messages.success(request, msg)
        return redirect("event_details", pk=event.pk)

    return render(request, "MyLife/event_invite_form.html",
                  {"form": form, "event": event})

def respond_event_invite(request, iid, decision):
    """ let invitee accept or reject an event invite """
    try:
        invite = EventInvite.objects.select_related("event").get(pk=iid)
    except EventInvite.DoesNotExist:
        messages.error(request, "Invite not found.")
        return redirect("calendar")

    if invite.invitee != request.user.project_profile:
        messages.error(request, "That invite isn’t for you.")
        return redirect("calendar")

    if decision == "accept":
        request.user.project_profile.accept_event_collaborator(invite.event)
        messages.success(request, "You’re now on the event!")
    elif decision == "reject":
        invite.invite_status = "rejected"
        invite.save()
        messages.success(request, "Invite rejected.")
    return redirect("event_details", pk=invite.event.pk)

class InviteEventCollaboratorView(LoginRequiredMixin, View):
    """
    view to show a list of profiles and send event invites
    """
    template_name = "MyLife/invite_event_collaborator.html"

    def get_event(self, pk):
        # helper to fetch event
        return Event.objects.get(pk=pk)

    def get(self, request, pk):
        event = self.get_event(pk)
        # choose all other profiles as candidates
        candidates = Profile.objects.exclude(pk=request.user.project_profile.pk)
        return render(request, self.template_name, {
            "event": event,
            "candidates": candidates,
        })

    def post(self, request, pk):
        event = self.get_event(pk)
        inviter_profile = request.user.project_profile
        invitee_pk = request.POST.get("invitee_pk")
        try:
            invitee = Profile.objects.get(pk=invitee_pk)
        except Profile.DoesNotExist:
            # re-show form with error
            return render(request, self.template_name, {
                "event": event,
                "candidates": Profile.objects.exclude(pk=inviter_profile.pk),
                "error": "Selected user not found.",
            })

        # send the invite and go back to event page
        inviter_profile.add_event_collaborator(event, invitee)
        return redirect("event_details", pk=pk)