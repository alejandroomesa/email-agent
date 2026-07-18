# Gmail Classifier Agent

Agente que lee tu bandeja de Gmail, clasifica cada email según categorías
que tú defines (en base a tus intereses) y les aplica la etiqueta
correspondiente en Gmail. Guarda un registro de auditoría de cada email
procesado para evitar reclasificar lo mismo dos veces.

Es un servicio standalone en Python: usa un LLM local vía
[Ollama](https://ollama.com/) para clasificar (ningún email sale de tu
máquina) y se conecta a Gmail por IMAP/SMTP con una contraseña de
aplicación, sin pasar por Google Cloud Console.

## Estado actual: MVP (fase 1)

Lo que hace hoy:

- Lee mensajes nuevos de tu bandeja (`in:inbox is:unread` por defecto).
- Clasifica cada uno con un modelo local de Ollama, según las categorías
  de `app/categories.yaml`.
- Aplica la etiqueta de Gmail correspondiente (Gmail la crea sola si no
  existe).
- Registra cada clasificación en una base SQLite local para no volver a
  procesar el mismo email en la siguiente ejecución.

Lo que **todavía no** hace (fases siguientes):

- Generar un borrador de respuesta con IA.
- Exponer un flujo de aprobación/rechazo humano.
- Enviar emails.

## Arquitectura

```
app/
  main.py          FastAPI: endpoints /sync, /processed, /categories
  models.py        Modelos Pydantic (EmailMessage, Category, ClassificationResult, ProcessedRecord)
  config.py        Settings (env vars vía .env) + carga de categories.yaml
  gmail_client.py  Lectura y etiquetado por IMAP (contraseña de aplicación)
  classifier.py    Clasificación vía Ollama (salida JSON estructurada)
  storage.py       SQLite: idempotencia + auditoría
  categories.yaml  Tus categorías de clasificación (editable)
tests/             Tests unitarios con mocks (no llaman a Gmail ni a Ollama reales)
```

### Flujo de `POST /sync`

1. Busca mensajes nuevos en Gmail por IMAP (`gmail_client.list_new_messages`,
   usando la sintaxis de búsqueda de Gmail vía `X-GM-RAW`).
2. Por cada mensaje, si ya fue procesado antes (según `storage`), se
   salta.
3. Se clasifica con Ollama, pidiendo salida JSON estructurada
   (`{category, confidence, reasoning}`).
4. Se aplica la etiqueta de Gmail de esa categoría al mensaje
   (`X-GM-LABELS` por IMAP; Gmail la crea automáticamente si no existe).
5. Se guarda el resultado en SQLite (`data/agent.db`).

## Requisitos previos

1. **Python 3.11+**
2. **Ollama** instalado y corriendo, con un modelo descargado:
   ```
   ollama pull llama3.1
   ```
3. **Contraseña de aplicación de Gmail** (no hace falta Google Cloud
   Console ni facturación):
   - Activa la verificación en 2 pasos en tu cuenta de Google, si no la
     tienes ya.
   - Genera una contraseña de aplicación en
     [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
   - Comprueba que el acceso IMAP esté activado en Gmail
     (Configuración → Reenvío y POP/IMAP → Habilitar IMAP).

## Instalación

```bash
python -m venv .venv
./.venv/Scripts/python -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt   # macOS/Linux
```

## Configuración

Copia `.env.example` como `.env` y completa tus credenciales:

```
GMAIL_ADDRESS=tu_correo@gmail.com
GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx
```

`.env` está en `.gitignore`: nunca se sube al repositorio.

Edita `app/categories.yaml` con tus propias categorías. Cada una tiene:

- `name`: nombre corto interno.
- `description`: se le pasa tal cual al LLM — describe bien qué tipo de
  email cae en esta categoría.
- `gmail_label`: nombre de la etiqueta que se aplicará en Gmail.

Variables de entorno opcionales (todas tienen un valor por defecto
razonable):

| Variable          | Default               | Qué controla                            |
|-------------------|------------------------|------------------------------------------|
| `OLLAMA_MODEL`    | `llama3.1`             | Modelo de Ollama usado para clasificar   |
| `GMAIL_QUERY`     | `in:inbox is:unread`   | Búsqueda de Gmail (sintaxis Gmail normal)|
| `CATEGORIES_PATH` | `app/categories.yaml`  | Ruta al archivo de categorías            |
| `DB_PATH`         | `data/agent.db`        | Base SQLite de auditoría                 |

## Uso

```bash
./.venv/Scripts/python -m uvicorn app.main:app --reload
```

Endpoints (documentación interactiva en `http://localhost:8000/docs`):

- `GET /categories` — lista las categorías configuradas.
- `POST /sync` — ejecuta el pipeline: lee, clasifica y etiqueta emails
  nuevos. Devuelve un resumen (cuántos procesados, por categoría).
- `GET /processed?limit=50` — lista las últimas clasificaciones
  guardadas, para revisar si el modelo está acertando.

## Tests

```bash
./.venv/Scripts/python -m pytest -v
```

Todos los tests usan mocks (de Ollama y de IMAP) — no requieren conexión
real ni credenciales.

## Roadmap

- [x] Fase 1 — Lectura + clasificación + etiquetado (MVP actual).
- [ ] Fase 2 — Generación de borrador de respuesta con IA.
- [ ] Fase 2 — Endpoints de aprobación/rechazo humano
      (`POST /approve/{id}`, `POST /reject/{id}`).
- [ ] Fase 2 — Envío del email tras la aprobación humana.
