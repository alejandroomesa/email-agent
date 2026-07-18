import base64

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from app import config
from app.models import EmailMessage


def _get_credentials() -> Credentials:
    creds = None
    if config.TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(config.TOKEN_PATH), config.GMAIL_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(config.CREDENTIALS_PATH), config.GMAIL_SCOPES
            )
            creds = flow.run_local_server(port=0)

        config.TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        config.TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    return creds


class GmailClient:
    def __init__(self):
        self._service = build("gmail", "v1", credentials=_get_credentials())
        self._label_cache: dict[str, str] = {}

    def list_new_messages(self, query: str = config.GMAIL_QUERY) -> list[EmailMessage]:
        message_ids: list[str] = []
        request = self._service.users().messages().list(userId="me", q=query)
        while request is not None:
            response = request.execute()
            message_ids.extend(m["id"] for m in response.get("messages", []))
            request = self._service.users().messages().list_next(request, response)

        return [self._get_message(message_id) for message_id in message_ids]

    def _get_message(self, message_id: str) -> EmailMessage:
        raw = (
            self._service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        headers = {h["name"].lower(): h["value"] for h in raw["payload"].get("headers", [])}

        return EmailMessage(
            message_id=raw["id"],
            thread_id=raw["threadId"],
            sender=headers.get("from", ""),
            subject=headers.get("subject", ""),
            body=_extract_plain_text(raw["payload"]),
        )

    def ensure_label(self, name: str) -> str:
        if name in self._label_cache:
            return self._label_cache[name]

        labels = self._service.users().labels().list(userId="me").execute().get("labels", [])
        for label in labels:
            if label["name"] == name:
                self._label_cache[name] = label["id"]
                return label["id"]

        created = (
            self._service.users()
            .labels()
            .create(
                userId="me",
                body={
                    "name": name,
                    "labelListVisibility": "labelShow",
                    "messageListVisibility": "show",
                },
            )
            .execute()
        )
        self._label_cache[name] = created["id"]
        return created["id"]

    def apply_label(self, message_id: str, label_id: str) -> None:
        self._service.users().messages().modify(
            userId="me", id=message_id, body={"addLabelIds": [label_id]}
        ).execute()


def _extract_plain_text(payload: dict) -> str:
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return _decode(payload["body"]["data"])

    for part in payload.get("parts", []):
        text = _extract_plain_text(part)
        if text:
            return text

    return ""


def _decode(data: str) -> str:
    return base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="replace")
