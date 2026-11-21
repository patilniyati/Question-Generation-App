import json
from types import SimpleNamespace

import pytest

from helpers import make_question
from src.config import GROQ_MODEL
from src.mcq_generator import generate_mcqs, get_groq_client, parse_mcq_response
from src.prompts import MCQ_USER_PROMPT


class FakeGroq:
    """Records the request and returns a canned model response."""

    def __init__(self, content: str):
        self.calls = []
        self._content = content
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        message = SimpleNamespace(content=self._content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_parse_valid_response():
    payload = json.dumps({"questions": [make_question(0), make_question(1)]})
    assert len(parse_mcq_response(payload)) == 2


def test_parse_missing_questions_key_gives_empty_list():
    assert parse_mcq_response("{}") == []


def test_parse_invalid_json_raises():
    with pytest.raises(ValueError, match="not valid JSON"):
        parse_mcq_response("Sure! Here are your questions:")


def test_parse_non_list_questions_raises():
    with pytest.raises(ValueError, match="question list"):
        parse_mcq_response('{"questions": "oops"}')


def test_get_groq_client_requires_key():
    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        get_groq_client("")


def test_prompt_template_formats_without_brace_errors():
    prompt = MCQ_USER_PROMPT.format(
        num_questions=3, difficulty="easy", topic="Cells", chunk="Some text."
    )
    assert "Create 3 multiple-choice questions" in prompt
    assert "Some text." in prompt
    assert '"questions"' in prompt  # the JSON example survived formatting


def test_generate_mcqs_sends_expected_request_and_parses_reply():
    client = FakeGroq(json.dumps({"questions": [make_question(0)]}))

    result = generate_mcqs(
        client, chunk="Chloroplasts do photosynthesis.", num_questions=4,
        difficulty="hard", topic="Plants",
    )

    assert len(result) == 1
    request = client.calls[0]
    assert request["model"] == GROQ_MODEL
    assert request["response_format"] == {"type": "json_object"}
    user_prompt = request["messages"][1]["content"]
    assert "Create 4 multiple-choice questions" in user_prompt
    assert "hard" in user_prompt
    assert "Plants" in user_prompt
    assert "Chloroplasts do photosynthesis." in user_prompt


def test_generate_mcqs_defaults_topic_to_general():
    client = FakeGroq('{"questions": []}')

    generate_mcqs(client, chunk="text", num_questions=3, difficulty="easy", topic="")

    assert "General" in client.calls[0]["messages"][1]["content"]
