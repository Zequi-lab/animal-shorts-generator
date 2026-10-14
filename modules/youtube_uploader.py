import os
import pickle
import json
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload
from modules.email_notifier import EmailNotifier

class YouTubeUploader:
    def __init__(self, secrets_file="client_secrets.json", token_file="token.json"):
        self.secrets_file = secrets_file
        self.token_file = token_file
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        self.api_service_name = "youtube"
        self.api_version = "v3"
        self.youtube = None

    def authenticate(self):
        """
        Authenticates the user using OAuth 2.0.
        Saves tokens to a JSON file for cross-device compatibility.
        """
        credentials = None
        
        # Load existing credentials from JSON
        if os.path.exists(self.token_file):
            print(f"[YouTube] Loading saved credentials from {self.token_file}...")
            try:
                credentials = Credentials.from_authorized_user_file(self.token_file, self.scopes)
            except Exception as e:
                print(f"[YouTube] Error loading JSON credentials: {e}")

        # Migration from pickle to JSON if token.json doesn't exist but token.pickle does
        if not credentials and os.path.exists("token.pickle"):
            print("[YouTube] Migrating legacy token.pickle to JSON...")
            try:
                with open("token.pickle", 'rb') as token:
                    credentials = pickle.load(token)
            except Exception as e:
                print(f"[YouTube] Could not load legacy pickle: {e}")

        # Refresh or Create new credentials
        if not credentials or not credentials.valid:
            try:
                if credentials and credentials.expired and credentials.refresh_token:
                    print("[YouTube] Refreshing access token...")
                    credentials.refresh(Request())
            except Exception as e:
                print(f"[YouTube] Refresh failed ({e}). Token might be revoked. Forcing re-auth...")
                credentials = None

            if not credentials or not credentials.valid:
                print("[YouTube] Starting OAuth flow. A browser window will open...")
                if not os.path.exists(self.secrets_file):
                    print(f"[YouTube] Error: '{self.secrets_file}' not found. Please provide credentials.")
                    EmailNotifier().send_alert(
                        "Falla Crítica de Configuración Youtube",
                        f"El archivo '{self.secrets_file}' no fue encontrado. El sistema automático no logró iniciar sesión como ezealienzequi@gmail.com."
                    )
                    return False
                
                try:
                    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                        self.secrets_file, self.scopes)
                    
                    # Auto-select the user's account to avoid the account chooser screen
                    credentials = flow.run_local_server(
                        port=0,
                        login_hint='ezealienzequi@gmail.com',
                        authorization_prompt_message='Please visit this URL to authorize this application: {url}'
                    )
                except Exception as e:
                    print(f"[YouTube] OAuth flow failed or was cancelled: {e}")
                    print("[YouTube] TIP: If you see a 'site can't be reached' error, try clearing your browser cache or using an Incognito window.")
                    EmailNotifier().send_alert(
                        "Alerta de Autorización (Google OAuth Expirado)",
                        f"El inicio de sesión falló automáticamente.\n\n"
                        f"Si estás ejecutando en estado desatendido y ves este error, es altamente probable que Google haya caducado tu token tras 7 días debido a que tu Aplicación en Google Cloud está marcada como 'Testing' (En Pruebas).\n\n"
                        f"Por favor, ve a Google Cloud Platform > Pantalla de Consentimiento de OAuth > y haz clic en 'Publicar la aplicación' (In Production). Esto hará que el acceso nunca se caduque y no necesites presionar 'Confirmar/Continuar' nunca más.\n\nError Técnico:\n{str(e)}"
                    )
                    return False
            
            # Save the credentials for the next run as JSON
            if credentials:
                with open(self.token_file, 'w') as token:
                    token.write(credentials.to_json())
                
                # Cleanup the old pickle file if it exists
                if os.path.exists("token.pickle"):
                    try:
                        os.remove("token.pickle")
                    except:
                        pass

        try:
            if credentials:
                self.youtube = googleapiclient.discovery.build(
                    self.api_service_name, self.api_version, credentials=credentials)
                return True
            return False
        except Exception as e:
            print(f"[YouTube] Error building service: {e}")
            EmailNotifier().send_alert(
                "Error al construir el Servicio de YouTube",
                f"Las credenciales locales son válidas pero la API de YouTube falló al conectarse.\nError:\n{str(e)}"
            )
            return False

    def upload_video(self, file_path, title, description, tags, category_id="27", privacy_status="public"):
        """
        Uploads the video to YouTube.
        privacy_status: 'private', 'public', or 'unlisted'
        """
        if not self.youtube:
            if not self.authenticate():
                print("[YouTube] Authentication failed. Falling back to Mock.")
                # Since authenticate already sends an alert on failure, we don't duplicate it.
                return "MOCK_VIDEO_ID"

        print(f"--- UPLOADING TO YOUTUBE: {title} ---")
        
        if not os.path.exists(file_path):
            print(f"[YouTube] Error: Video file not found at {file_path}")
            EmailNotifier().send_alert(
                f"Falla al subir video (Archivo no encontrado)",
                f"Se intentó subir el video para '{title}' a YouTube, pero el archivo '{file_path}' no existe en el sistema."
            )
            return None

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False, # Important for shorts
            }
        }

        try:
            # Chunk size: 4MB
            media = MediaFileUpload(file_path, chunksize=4*1024*1024, resumable=True, mimetype="video/mp4")
            
            request = self.youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )
            
            print("[YouTube] Uploading...")
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"[YouTube] Upload progress: {int(status.progress() * 100)}%")
            
            print("[YouTube] Upload Complete!")
            return response.get("id")
            
        except googleapiclient.errors.HttpError as e:
            print(f"[YouTube] An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
            EmailNotifier().send_alert(
                f"Falla HTTP de YouTube al subir: {title}",
                f"Surgió un error HTTP de la API de YouTube al subir el video (Típicamente un error de Quota, Título duplicado, o conexión perdida).\nCódigo de Error: {e.resp.status}\nRespuesta Detallada:\n{e.content.decode('utf-8') if isinstance(e.content, bytes) else e.content}"
            )
            return None
        except Exception as e:
            print(f"[YouTube] Unexpected error during upload: {e}")
            EmailNotifier().send_alert(
                f"Error Crítico al subir video: {title}",
                f"Surgió un error inesperado (posiblemente de conexión local) al subir el video a YouTube.\nError:\n{str(e)}"
            )
            return None
