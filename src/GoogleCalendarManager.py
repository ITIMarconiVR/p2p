from requests_oauthlib import OAuth2Session
from googleapiclient.discovery import build
from datetime import datetime, timedelta


GOOGLE_CLIENT_ID="717588494889-3ecmb3rfivadscacgnj98cpd7d7ko0ar.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET ="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"


class GoogleCalendarManager:
    def __init__(self, google_token):
        """
        Initialize the calendar manager with OAuth token
        """
        self.oauth_session = OAuth2Session(GOOGLE_CLIENT_ID)
        self.oauth_session.token = google_token
        
        # Create service
        credentials = {
            'token': google_token['access_token'],
            'refresh_token': google_token.get('refresh_token'),
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
        }
        self.service = build('calendar', 'v3', credentials=credentials)

    def create_lesson_event(self, event_details):
        """
        Create a calendar event for a lesson
        """
        try:
            # Convert time format
            start_time = datetime.strptime(event_details['data'], '%Y-%m-%d')
            if event_details['ora'] == 1:
                start_time = start_time.replace(hour=13, minute=40)
            else:  # ora == 2
                start_time = start_time.replace(hour=14, minute=30)
            
            end_time = start_time + timedelta(minutes=50)

            # Create attendee list
            attendees = []
            if event_details.get('matricolaT'):
                attendees.append({
                    'email': f"{event_details['matricolaT']}@studenti.marconiverona.edu.it",
                    'responseStatus': 'accepted'
                })
            if event_details.get('matricolaP'):
                attendees.append({
                    'email': f"{event_details['matricolaP']}@studenti.marconiverona.edu.it",
                    'responseStatus': 'accepted'
                })

            event = {
                'summary': f"Lezione P2P - {event_details.get('materiaL', 'Materia TBD')}",
                'location': event_details.get('aulaL', 'TBD'),
                'description': (
                    f"Materia: {event_details.get('materiaL', '')}\n"
                    f"Argomenti: {event_details.get('argomenti', '')}\n"
                ),
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'Europe/Rome',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'Europe/Rome',
                },
                'attendees': attendees,
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 30},
                    ],
                },
                'guestsCanModify': False,
                'guestsCanInviteOthers': False,
            }

            # Create the event and send emails to all attendees
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()

            return True, created_event['id']

        except Exception as e:
            print(f"Error creating calendar event: {e}")
            return False, str(e)

    def delete_event(self, event_id):
        """
        Delete a calendar event
        """
        try:
            # Delete the event and notify all attendees
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            return True
        except Exception as e:
            print(f"Error deleting calendar event: {e}")
            return False