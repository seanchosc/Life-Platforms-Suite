## Create app-specific URL:
# MyLife/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views 
from .views import * # import everything from views
from . import views # For calendar
urlpatterns = [
    # map the URL (empty string) to the view
    
    path('', BaseView.as_view(), name='base'), # base view
    path('home', HomeView.as_view(), name='home'), #home view
    path('dashboard/', ShowUserDashboardView.as_view(), name='user_dashboard'), # user dashboard showing upcoming events and invites
    # Event and profile views
    path('events/new/', CreateEventView.as_view(), name='create_event'), # event creation form
    path('events/<int:pk>/edit/', UpdateEventView.as_view(), name='update_event'), # event update form
    path('profile/create/', CreateProfileView.as_view(), name='create_profile'), # profile creation form
    path('profile/edit/', UpdateProfileView.as_view(), name='update_profile'), # profile update form
    path('profile/', ShowProfilePageView.as_view(), name='show_profile'), # show own profile
    path('profile/<int:pk>/',ShowProfilePageView.as_view(), name='show_person'), #show a given users profile by their pk


    path('login/', auth_views.LoginView.as_view(template_name='MyLife/login.html'), name='login'), ## show login template when logging in
	path('logout/',CustomLogoutView.as_view(next_page='logout_confirmation'),name='logout'), ##  show view at logout_confirmation when logging out
    path('logout_confirmation/', LogoutRedirectView.as_view(), name='logout_confirmation'), ## show the LogoutRedirect view when redirected after logout
    path('register/', UserRegistrationView.as_view(), name='register'), ## Show the Registration view

    # event-detail page
    path('events/<int:pk>/', ShowEventDetailsView.as_view(), name='event_details'), #shows all event details
    path('events/<int:event_pk>/posts/',CreateEventPostView.as_view(),name='event_posts',), # view for creating a post on a given event by its event pk
    # MyLife/urls.py
    path('calendar/',views.CalendarView.as_view(), name='calendar'), # page that shows the calendar, # fullcalendar integration
    path('api/events/',views.EventJsonFeedView.as_view(), name='events_json'), # the json feed that fullcalendar queries

    path('profile/<int:pk>/invite/', send_collab_invite, name='send_collab_invite'), # path for when sending a collaborator invite
    path('collab/<int:cid>/respond/<str:decision>/',respond_collab_invite,name='respond_collab_invite'), # path for when responding to a collaborator invite

    # event-invite
    path('events/<int:pk>/invite/',InviteEventCollaboratorView.as_view(),name='send_event_invite',),# path for when sending an event invite
    path('eventinvite/<int:iid>/respond/<str:decision>/',respond_event_invite,name='respond_event_invite'), # path for when responding to an event invite
    
]