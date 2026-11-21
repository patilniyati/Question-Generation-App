from src.config import CHUNK_OVERLAP, CHUNK_SIZE
from src.text_chunker import chunk_text


def test_empty_and_whitespace_text_gives_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []


def test_short_text_is_a_single_stripped_chunk():
    assert chunk_text("  hello world  ") == ["hello world"]


def test_text_exactly_at_limit_is_a_single_chunk():
    text = "a" * CHUNK_SIZE
    assert chunk_text(text) == [text]


def test_long_text_is_split_and_no_chunk_exceeds_limit():
    text = " ".join(f"word{i}" for i in range(2000))
    chunks = chunk_text(text)

    assert len(chunks) > 1
    assert all(len(chunk) <= CHUNK_SIZE for chunk in chunks)


def test_consecutive_chunks_overlap():
    text = " ".join(f"word{i}" for i in range(2000))
    chunks = chunk_text(text)

    for previous, current in zip(chunks, chunks[1:]):
        assert current[:50] in previous


def test_every_word_survives_chunking():
    words = [f"word{i}" for i in range(2000)]
    chunks = chunk_text(" ".join(words))

    chunked_words = {w for chunk in chunks for w in chunk.split()}
    assert set(words) <= chunked_words


def test_prefers_paragraph_break_when_past_half_the_chunk():
    first = ("Alpha sentence. " * 150).strip()  # ~2400 chars, past half of 3500
    text = first + "\n\n" + ("Beta sentence. " * 300)

    chunks = chunk_text(text)

    assert chunks[0] == first
    assert "Beta" not in chunks[0]


def test_falls_back_to_sentence_break():
    text = "One sentence ends here. " * 400  # no blank lines at all
    chunks = chunk_text(text)

    assert len(chunks) > 1
    assert chunks[0].endswith(".")


def test_custom_size_and_overlap():
    text = "x" * 100
    chunks = chunk_text(text, chunk_size=40, overlap=10)

    assert all(len(chunk) <= 40 for chunk in chunks)
    assert chunks[0] == "x" * 40


def test_terminates_even_if_overlap_exceeds_chunk_size():
    # Degenerate settings must not hang; progress is at least one char per step.
    chunks = chunk_text("y" * 100, chunk_size=10, overlap=20)
    assert len(chunks) > 1


def test_default_settings_are_sane():
    assert 0 < CHUNK_OVERLAP < CHUNK_SIZE
