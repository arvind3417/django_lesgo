# Import the required modules and classes
import os
import google_auth_oauthlib.flow
import google.oauth2.credentials
from django.shortcuts import redirect
from django.views import View
from django.http import HttpResponse
import googleapiclient.discovery
from rest_framework.decorators import api_view

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
redirect_uri='http://127.0.0.1:8000/rest/v1/calendar/redirect/'
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'

# Define the GoogleCalendarInitView class
class GoogleCalendarInitView(View):
    def get(self, request):
        # Create the OAuth2 flow instance
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            'E:\django_lesgo\google_calendar_integration\calendar_integration\client_secret_549511539034-ni42i2b3jjjjn29hp2d775rcdat7rotk.apps.googleusercontent.com.json',
            scopes=['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.readonly',
                'https://www.googleapis.com/auth/calendar.events.readonly'],
            # redirect_uri='http://localhost:8000/rest/v1/calendar/init/'
        )
        flow.redirect_uri = redirect_uri
        # Generate the authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        request.session['state'] = state
        
        print("Authorization URL:", authorization_url)  # Debugging statement
        
        # Redirect the user to the authorization URL
        return HttpResponse(authorization_url)

# Define the GoogleCalendarRedirectView class
class GoogleCalendarRedirectView(View):
    def get(self, request):
        state = request.session['state']
        
        if state is None:
            return HttpResponse('No state')
        # Create the OAuth2 flow instance
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            'E:\django_lesgo\google_calendar_integration\calendar_integration\client_secret_549511539034-ni42i2b3jjjjn29hp2d775rcdat7rotk.apps.googleusercontent.com.json',
            scopes=['https://www.googleapis.com/auth/calendar'],state = state
        )
        flow.redirect_uri = redirect_uri
        # Fetch the authorization code from the request
        # code = request.GET.get('code')
        authorization_response = request.get_full_path()
        flow.fetch_token(authorization_response=authorization_response)
        credentials = flow.credentials
        request.session['credentials'] = credentials_to_dict(credentials)
        if 'credentials' not in request.session:
            return redirect('v1/calendar/init')

    # Load credentials from the session.
        credentials = google.oauth2.credentials.Credentials(
            **request.session['credentials'])

        # Use the Google API Discovery Service to build client libraries, IDE plugins,
        # and other tools that interact with Google APIs.
        # The Discovery API provides a list of Google APIs and a machine-readable "Discovery Document" for each API
        service = googleapiclient.discovery.build(
            API_SERVICE_NAME, API_VERSION, credentials=credentials)

        # Returns the calendars on the user's calendar list
        calendar_list = service.calendarList().list().execute()

        # Getting user ID which is his/her email address
        calendar_id = calendar_list['items'][0]['id']

        # Getting all events associated with a user ID (email address)
        events = service.events().list(calendarId=calendar_id).execute()

        events_list_append = []
        if not events['items']:
            print('No data found.')
            return HttpResponse({"message": "No data found or user credentials invalid."})
        else:
            for events_list in events['items']:
                events_list_append.append(events_list)

        # return Response({"error": "calendar event aren't here"})
        return HttpResponse({"events": events_list_append})
        # if code:
        #     # Exchange the authorization code for an access token
        #     flow.fetch_token(
        #         authorization_response=request.build_absolute_uri(),
        #         code=code
        #     )
            
        #     # Get the credentials containing the access token
        #     credentials = flow.credentials
            
        #     # Use the credentials to make API requests to Google Calendar API
        #     # Implement the logic to retrieve the list of events
        #     events = get_calendar_events(credentials)
            
        #     # Return the response with the events data
        #     return HttpResponse(f"Calendar Events: {events}")

        # Handle the case when there is no authorization code in the request
        # return HttpResponse("Authorization code not found")

# def get_calendar_events(credentials):
#     # Build the Google Calendar API client using the provided credentials
#     service = build('calendar', 'v3', credentials=credentials)

#     # Make a request to retrieve the list of events from the user's calendar
#     events_result = service.events().list(calendarId='primary', maxResults=10).execute()
#     events = events_result.get('items', [])

#     # Extract relevant information from the events and return the list
#     event_list = []
#     for event in events:
#         event_list.append({
#             'id': event['id'],
#             'summary': event['summary'],
#             'start': event['start'].get('dateTime', event['start'].get('date')),
#             'end': event['end'].get('dateTime', event['end'].get('date'))
#         })

#     return event_list
def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}