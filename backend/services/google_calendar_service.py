import os.path
import logging
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_CALENDAR_AVAILABLE = True
except ImportError:
    GOOGLE_CALENDAR_AVAILABLE = False
from datetime import datetime, timedelta

logger = logging.getLogger("GoogleCalendarService")

# Escopos necessários para ler e escrever na agenda
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarService:
    def __init__(self):
        self.creds = None
        self.token_path = 'token.json'
        self.service = None

    def _authenticate(self):
        """Gerencia a autenticação e retorna as credenciais."""
        if not GOOGLE_CALENDAR_AVAILABLE:
            return None
        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                # Se não houver token ou expirar sem refresh, precisamos do flow manual
                logger.error("❌ Credenciais do Google Calendar ausentes ou inválidas. Execute auth_google_calendar.py")
                return None
            
            with open(self.token_path, 'w') as token:
                token.write(self.creds.to_json())
        
        return self.creds

    def get_service(self):
        """Retorna o objeto do serviço da API do Google Calendar."""
        if not GOOGLE_CALENDAR_AVAILABLE:
            return None
        if not self.service:
            creds = self._authenticate()
            if creds:
                self.service = build('calendar', 'v3', credentials=creds)
        return self.service

    async def add_event(self, title: str, description: str, start_time: datetime, duration_minutes: int = 30):
        """Adiciona um evento ao Google Calendar principal."""
        if not GOOGLE_CALENDAR_AVAILABLE:
            return False
        service = self.get_service()
        if not service:
            return False

        end_time = start_time + timedelta(minutes=duration_minutes)
        
        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat() + 'Z', # UTC
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat() + 'Z',
                'timeZone': 'UTC',
            },
            'reminders': {
                'useDefault': True,
            },
        }

        try:
            event = service.events().insert(calendarId='primary', body=event).execute()
            logger.info(f"✅ Evento criado no Google Calendar: {event.get('htmlLink')}")
            return True
        except HttpError as error:
            logger.error(f"Erro ao criar evento no Google: {error}")
            return False

    async def list_upcoming_events(self, max_results: int = 5):
        """Lista os próximos eventos da agenda Google."""
        if not GOOGLE_CALENDAR_AVAILABLE:
            return []
        service = self.get_service()
        if not service:
            return []

        now = datetime.utcnow().isoformat() + 'Z'
        try:
            events_result = service.events().list(calendarId='primary', timeMin=now,
                                                maxResults=max_results, singleEvents=True,
                                                orderBy='startTime').execute()
            return events_result.get('items', [])
        except HttpError as error:
            logger.error(f"Erro ao buscar eventos no Google: {error}")
            return []

google_calendar_service = GoogleCalendarService()
