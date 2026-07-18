# Gmail Classifier Agent

Agente que lee tu bandeja de Gmail, clasifica cada email según categorías
que vos definís (en base a tus intereses) y les aplica la label
correspondiente en Gmail. Guarda un registro de auditoría de cada email
procesado para evitar reclasificar lo mismo dos veces.

Este es un servicio standalone en Python: usa un LLM local vía
[Ollama](https://ollama.com/) para clasificar (nada de tus emails sale de
tu máquina) y la Gmail API oficial para leer/etiquetar.

## Estado actual: MVP (fase 1)

Lo que hace hoy:

- Lee mensajes nuevos de tu bandeja (`in:inbox is:unread` por default).
- Clasifica cada uno con un modelo local de Ollama, según las categorías
  de `app/categories.yaml`.
- Crea (si hace falta) y aplica la label de Gmail correspondiente.
- Registra cada clasificación en una base SQLite local para no volver a
  procesar el mismo email en la próxima corrida.

Lo que **todavía no** hace (fases siguientes):

- Generar un borrador de respuesta con IA.
- Exponer un flujo de aprobación/rechazo humano.
- Enviar emails.

## Arquitectura

```
app/
  main.py          FastAPI: endpoints /sync, /processed, /categories
  models.py        Modelos Pydantic (EmailMessage, Category, ClassificationResult, ProcessedRecord)
  config.py        Settings (env vars) + carga de categories.yaml
  gmail_client.py  Auth OAuth2 + lectura de mensajes + gestión de labels
  classifier.py    Clasificación vía Ollama (salida JSON estructurada)
  storage.py       SQLite: idempotencia + auditoría
  categories.yaml  Tus categorías de clasificación (editable)
tests/             Tests unitarios con mocks (no llaman a Gmail ni a Ollama reales)
```

### Flujo de `POST /sync`

1. Busca mensajes nuevos en Gmail (`gmail_client.list_new_messages`).
2. Por cada mensaje, si ya fue procesado antes (según `storage`), se
   salta.
3. Se clasifica con Ollama, pidiendo salida JSON estructurada
   (`{category, confidence, reasoning}`).
4. Se asegura que exista la label de Gmail de esa categoría (se crea si
   falta) y se aplica al mensaje.
5. Se guarda el resultado en SQLite (`data/agent.db`).

## Requisitos previos

1. **Python 3.11+**
2. **Ollama** instalado y corriendo, con un modelo bajado:
   ```
   ollama pull llama3.1
   ```
3. **Credenciales de Gmail API** (OAuth2, tipo "Desktop app"):
   - Crear un proyecto en [Google Cloud Console](https://console.cloud.google.com/).
   - Habilitar la Gmail API.
   - Crear credenciales OAuth de tipo "Desktop app" y descargar el JSON.
   - Guardarlo como `credentials/client_secret.json` en la raíz del
     proyecto (esa carpeta está en `.gitignore`, no se sube a ningún
     lado).

## Instalación

```bash
python -m venv .venv
./.venv/Scripts/python -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt   # macOS/Linux
```

## Configuración

Editá `app/categories.yaml` con tus propias categorías. Cada una tiene:

- `name`: nombre corto interno.
- `description`: se le pasa tal cual al LLM — describí bien qué tipo de
  email cae en esta categoría.
- `gmail_label`: nombre de la label que se va a crear/aplicar en Gmail.

Variables de entorno opcionales (todas tienen default razonable):

| Variable               | Default                              | Qué controla                          |
|-------------------------|---------------------------------------|----------------------------------------|
| `OLLAMA_MODEL`          | `llama3.1`                            | Modelo de Ollama usado para clasificar |
| `GMAIL_QUERY`           | `in:inbox is:unread`                  | Query de Gmail para buscar mensajes    |
| `CATEGORIES_PATH`       | `app/categories.yaml`                 | Ruta al archivo de categorías          |
| `GMAIL_CREDENTIALS_PATH`| `credentials/client_secret.json`      | Credenciales OAuth descargadas         |
| `GMAIL_TOKEN_PATH`      | `credentials/token.json`              | Token cacheado tras el primer login    |
| `DB_PATH`               | `data/agent.db`                       | Base SQLite de auditoría               |

## Uso

```bash
./.venv/Scripts/python -m uvicorn app.main:app --reload
```

La primera vez que se ejecuta `/sync` se abre el navegador para el
consentimiento OAuth de Gmail; el token queda cacheado y no vuelve a
pedirse.

Endpoints (documentación interactiva en `http://localhost:8000/docs`):

- `GET /categories` — lista las categorías configuradas.
- `POST /sync` — corre el pipeline: lee, clasifica y etiqueta emails
  nuevos. Devuelve un resumen (cuántos procesados, por categoría).
- `GET /processed?limit=50` — lista las últimas clasificaciones
  guardadas, para revisar si el modelo está acertando.

## Tests

```bash
./.venv/Scripts/python -m pytest -v
```

Todos los tests usan mocks (de Ollama y de la Gmail API) — no requieren
conexión real ni credenciales.

## Roadmap

- [x] Fase 1 — Lectura + clasificación + etiquetado (MVP actual).
- [ ] Fase 2 — Generación de borrador de respuesta con IA.
- [ ] Fase 2 — Endpoints de aprobación/rechazo humano
      (`POST /approve/{id}`, `POST /reject/{id}`).
- [ ] Fase 2 — Envío del email tras la aprobación humana.
