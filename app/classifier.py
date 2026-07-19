import ollama

from app import config
from app.models import Category, ClassificationResult, EmailMessage

SYSTEM_PROMPT = """Eres un clasificador de emails. Vas a recibir un email y una \
lista de categorías posibles, cada una con una descripción. Elige la categoría \
que mejor describe el email y devuelve tu respuesta en el formato JSON pedido. \
El campo "category" debe ser exactamente uno de los nombres de categoría dados."""


def classify(email: EmailMessage, categories: list[Category]) -> ClassificationResult:
    categories_block = "\n".join(f"- {c.name}: {c.description}" for c in categories)

    user_prompt = (
        f"Categorías disponibles:\n{categories_block}\n\n"
        f"Email a clasificar:\n"
        f"De: {email.sender}\n"
        f"Asunto: {email.subject}\n"
        f"Cuerpo:\n{email.body[:4000]}"
    )

    response = ollama.chat(
        model=config.OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        format=ClassificationResult.model_json_schema(),
    )

    return ClassificationResult.model_validate_json(response.message.content)
