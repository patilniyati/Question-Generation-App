import pytest
from helpers import make_question

from src.validator import validate_question, validate_questions


def test_valid_question_has_no_errors():
    assert validate_question(make_question()) == []


@pytest.mark.parametrize("answer", ["A", "b", " c ", "D"])
def test_correct_answer_is_case_and_whitespace_insensitive(answer):
    assert validate_question(make_question(correct_answer=answer)) == []


@pytest.mark.parametrize("answer", ["E", "", "AB", "1"])
def test_invalid_correct_answer_is_rejected(answer):
    errors = validate_question(make_question(correct_answer=answer))
    assert "Correct answer must be A, B, C, or D." in errors


def test_missing_question_text():
    errors = validate_question(make_question(question="   "))
    assert "Question text is missing." in errors


def test_missing_option():
    question = make_question()
    question["options"]["C"] = ""
    assert "Option C is missing." in validate_question(question)


def test_duplicate_options_are_case_insensitive():
    question = make_question()
    question["options"]["B"] = "ALPHA"
    assert "Duplicate options found." in validate_question(question)


def test_missing_explanation():
    errors = validate_question(make_question(explanation=" "))
    assert "Explanation is missing." in errors


def test_options_must_be_an_object():
    errors = validate_question(make_question(options=["a", "b", "c", "d"]))
    assert errors == ["Options must be an object."]


def test_source_text_is_optional():
    question = make_question()
    del question["source_text"]
    assert validate_question(question) == []


def test_validate_questions_splits_valid_and_invalid_with_one_based_index():
    good = make_question(0)
    bad = make_question(1, correct_answer="Z")
    also_good = make_question(2)

    valid, invalid = validate_questions([good, bad, also_good])

    assert valid == [good, also_good]
    assert len(invalid) == 1
    assert invalid[0]["index"] == 2
    assert invalid[0]["question"] is bad
    assert "Correct answer must be A, B, C, or D." in invalid[0]["errors"]


def test_validate_questions_empty_list():
    assert validate_questions([]) == ([], [])


@pytest.mark.xfail(
    raises=AttributeError,
    strict=True,
    reason="Known gap: a null option (JSON null from the model) crashes the "
    "validator instead of being rejected. Fix in a later phase; strict=True "
    "makes this test fail once fixed so the marker gets removed.",
)
def test_null_option_is_reported_not_crashed():
    question = make_question()
    question["options"]["A"] = None
    assert "Option A is missing." in validate_question(question)
