from requests_oauthlib import OAuth2Session
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials


GOOGLE_CLIENT_ID="717588494889-3ecmb3rfivadscacgnj98cpd7d7ko0ar.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET ="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"


class GoogleCalendarManager:
    def __init__(self, google_token):
        """
        Initialize the calendar manager with OAuth token
        """
        try:
            credentials = Credentials(
                token=google_token['access_token'],
                refresh_token=None,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=GOOGLE_CLIENT_ID,
                client_secret=GOOGLE_CLIENT_SECRET,
                scopes=google_token['scope']
            )
            
            self.service = build('calendar', 'v3', credentials=credentials)
            
        except Exception as e:
            print(f"Error initializing calendar manager: {e}")
            raise

    def create_lesson_event(self, event_details):
        """
        Create a calendar event for a lesson in the primary calendars
        """
        try:
            # Parse date
            try:
                if isinstance(event_details['data'], str):
                    start_time = datetime.strptime(event_details['data'], '%Y-%m-%d')
                else:
                    start_time = event_details['data']
            except ValueError as e:
                print(f"Date parsing error: {e}")
                return False, "Invalid date format"

            # Parse time
            try:
                ora = int(event_details['ora'])
                if ora == 1:
                    start_time = start_time.replace(hour=13, minute=40)
                else:  # ora == 2
                    start_time = start_time.replace(hour=14, minute=30)
            except ValueError as e:
                print(f"Time parsing error: {e}")
                return False, "Invalid time format"
            
            end_time = start_time + timedelta(minutes=60)

            # Create attendee list
            attendees = []
            
            if event_details.get('matricolaT'):
                tutee_email = f"{event_details['matricolaT']}@studenti.marconiverona.edu.it"
                attendees.append({
                    'email': tutee_email,
                    'responseStatus': 'accepted'
                })
            
            if event_details.get('matricolaP'):
                tutor_email = f"{event_details['matricolaP']}@studenti.marconiverona.edu.it"
                attendees.append({
                    'email': tutor_email,
                    'responseStatus': 'accepted'
                })

            event = {
                'summary': f"Lezione P2P - {event_details.get('materiaL', 'Materia TBD')}",
                'location': event_details.get('aulaL', 'TBD'),
                'description': (
                    f"Materia: {event_details.get('materiaL', '')}\n"
                    f"Argomenti: {event_details.get('argomenti', '')}\n\n"
                    f"ATTENZIONE: L'eliminazione dell'evento dal calendario non comporta la cancellazione della lezione.\n"
                    f"Per cancellare la lezione è necessario utilizzare l'applicazione P2P."
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
                'colorId': '3',  # Dark purple color
                'guestsCanModify': False,  # Prevent attendees from modifying
                'guestsCanInviteOthers': False,  # Prevent inviting others
                'guestsCanSeeOtherGuests': True  # Allow seeing other attendees
            }

            # Create the event in primary calendar
            created_event = self.service.events().insert(
                calendarId='primary',  # Use primary calendar
                body=event,
                sendUpdates='none',  # Don't send updates to attendees
                conferenceDataVersion=0  # Disable conferencing
            ).execute()

            # Make all attendees organizers so they can delete the event
            # This is a workaround to ensure any participant can delete it
            try:
                # Update the event with explicit write access
                event_patch = {
                    'guestsCanModify': True,  # This is necessary for deletion to work
                    'guestsCanInviteOthers': False,
                    'transparentInvitations': False,
                    'attendeesOmitted': False
                }
                
                updated_event = self.service.events().patch(
                    calendarId='primary',
                    eventId=created_event['id'],
                    body=event_patch,
                    sendUpdates='none'  # Don't send updates
                ).execute()
                
                return True, created_event['id']
            except Exception as e:
                print(f"Error updating event permissions: {e}")
                # Still return success since the event was created
                return True, created_event['id']

        except Exception as e:
            print(f"Error creating calendar event: {e}")
            return False, str(e)

    def delete_event(self, event_id):
        """
        Delete a calendar event
        """
        try:
            self.service.events().delete(
                calendarId='primary',  # Use primary calendar
                eventId=event_id,
                sendUpdates='none'  # Don't send updates to attendees
            ).execute()
            return True
        except Exception as e:
            print(f"Error deleting calendar event: {e}")
            return False