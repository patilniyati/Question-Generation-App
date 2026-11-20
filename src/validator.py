VALID_ANSWERS = {"A", "B", "C", "D"}


def validate_question(question: dict) -> list[str]:
    errors = []

    if not question.get("question", "").strip():
        errors.append("Question text is missing.")

    options = question.get("options", {})

    if not isinstance(options, dict):
        errors.append("Options must be an object.")
        return errors

    for key in ["A", "B", "C", "D"]:
        if not options.get(key, "").strip():
            errors.append(f"Option {key} is missing.")

    correct_answer = question.get("correct_answer", "").strip().upper()

    if correct_answer not in VALID_ANSWERS:
        errors.append("Correct answer must be A, B, C, or D.")
    elif not options.get(correct_answer, "").strip():
        errors.append("Correct answer does not match any option.")

    option_values = [options.get(key, "").strip().lower() for key in VALID_ANSWERS]

    if len(option_values) != len(set(option_values)):
        errors.append("Duplicate options found.")

    if not question.get("explanation", "").strip():
        errors.append("Explanation is missing.")

    return errors


def validate_questions(questions: list[dict]) -> tuple[list[dict], list[dict]]:
    valid_questions = []
    invalid_questions = []

    for index, question in enumerate(questions, start=1):
        errors = validate_question(question)

        if errors:
            invalid_questions.append(
                {
                    "index": index,
                    "question": question,
                    "errors": errors,
                }
            )
        else:
            valid_questions.append(question)

    return valid_questions, invalid_questions