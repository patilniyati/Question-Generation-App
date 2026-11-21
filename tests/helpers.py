class FakeUpload:
    """Minimal stand-in for Streamlit's UploadedFile (name, size, getvalue)."""

    def __init__(self, name: str, data: bytes):
        self.name = name
        self.size = len(data)
        self._data = data

    def getvalue(self) -> bytes:
        return self._data


def make_question(index: int = 0, **overrides) -> dict:
    """A valid MCQ dict; the correct answer cycles A, B, C, D by index."""
    question = {
        "question": f"What is the answer to question number {index + 1}?",
        "options": {"A": "Alpha", "B": "Bravo", "C": "Charlie", "D": "Delta"},
        "correct_answer": "ABCD"[index % 4],
        "explanation": "Because the text says so.",
        "source_text": "The text says so.",
        "difficulty": "medium",
        "topic": "Testing",
    }
    question.update(overrides)
    return question
