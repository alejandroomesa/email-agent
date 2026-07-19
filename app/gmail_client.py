import email
import imaplib
import re
from contextlib import contextmanager
from email.header import decode_header, make_header
from email.message import Message

from app import config
from app.models import EmailMessage

IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993

_THRID_RE = re.compile(rb"X-GM-THRID (\d+)")


def _require_credentials() -> tuple[str, str]:
    if not config.GMAIL_ADDRESS or not config.GMAIL_APP_PASSWORD:
        raise RuntimeError(
            "Faltan GMAIL_ADDRESS y/o GMAIL_APP_PASSWORD. Generá una "
            "contraseña de aplicación en https://myaccount.google.com/apppasswords "
            "y definí ambas variables (ver .env.example)."
        )
    return config.GMAIL_ADDRESS, config.GMAIL_APP_PASSWORD


@contextmanager
def _imap_connection():
    address, app_password = _require_credentials()
    conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    try:
        conn.login(address, app_password)
        conn.select("INBOX")
        yield conn
    finally:
        conn.logout()


class GmailClient:
    def test_connection(self) -> None:
        """Intenta autenticarse por IMAP; lanza si las credenciales fallan."""
        with _imap_connection():
            pass

    def list_new_messages(self, query: str | None = None) -> list[EmailMessage]:
        query = query if query is not None else config.GMAIL_QUERY
        with _imap_connection() as conn:
            status, data = conn.uid("search", None, "X-GM-RAW", f'"{query}"')
            if status != "OK":
                raise RuntimeError(f"Búsqueda IMAP falló: {data}")

            uids = data[0].split()
            return [self._fetch_message(conn, uid) for uid in uids]

    def _fetch_message(self, conn: imaplib.IMAP4_SSL, uid: bytes) -> EmailMessage:
        status, data = conn.uid("fetch", uid, "(X-GM-THRID RFC822)")
        if status != "OK" or not data or data[0] is None:
            raise RuntimeError(f"No se pudo leer el mensaje {uid!r}: {data}")

        header, raw_email = data[0]
        thrid_match = _THRID_RE.search(header)

        parsed = email.message_from_bytes(raw_email)

        return EmailMessage(
            message_id=uid.decode(),
            thread_id=thrid_match.group(1).decode() if thrid_match else uid.decode(),
            sender=parsed.get("From", ""),
            subject=str(make_header(decode_header(parsed.get("Subject", "")))),
            body=_extract_plain_text(parsed),
        )

    def apply_label(self, message_id: str, label: str) -> None:
        with _imap_connection() as conn:
            conn.uid("STORE", message_id, "+X-GM-LABELS", f"({_quote(label)})")


def _extract_plain_text(msg: Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                return _decode_part(part)
        return ""

    if msg.get_content_type() == "text/plain":
        return _decode_part(msg)

    return ""


def _decode_part(part: Message) -> str:
    payload = part.get_payload(decode=True) or b""
    charset = part.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def _quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
