import json

from groq import Groq

from src.config import GROQ_MODEL
from src.prompts import MCQ_SYSTEM_PROMPT, MCQ_USER_PROMPT


def get_groq_client(api_key: str) -> Groq:
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing. Add it to your .env file.")

    return Groq(api_key=api_key)


def generate_mcqs(
    client: Groq,
    chunk: str,
    num_questions: int,
    difficulty: str,
    topic: str,
) -> list[dict]:
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": MCQ_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": MCQ_USER_PROMPT.format(
                    num_questions=num_questions,
                    difficulty=difficulty,
                    topic=topic or "General",
                    chunk=chunk,
                ),
            },
        ],
        temperature=0.3,
        max_completion_tokens=4096,
        response_format={"type": "json_object"},
    )

    raw_output = response.choices[0].message.content
    return parse_mcq_response(raw_output)


def parse_mcq_response(raw_output: str) -> list[dict]:
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as error:
        raise ValueError("The AI response was not valid JSON.") from error

    questions = data.get("questions", [])

    if not isinstance(questions, list):
        raise ValueError("AI response does not contain a question list.")

    return questions