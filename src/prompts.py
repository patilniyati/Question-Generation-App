MCQ_SYSTEM_PROMPT = """You are an expert teacher and academic assessment designer.
You create clear, factually accurate multiple-choice questions strictly from the supplied text.
Return only valid JSON. Do not include markdown, explanations outside JSON, or additional text."""

MCQ_USER_PROMPT = """Create {num_questions} multiple-choice questions from the document excerpt below.

Requirements:
- Use only information present in the excerpt.
- Each question must have exactly four options: A, B, C, and D.
- Exactly one option must be correct.
- Make distractors plausible but clearly incorrect.
- Do not create opinion-based or ambiguous questions.
- Write questions at {difficulty} difficulty.
- Focus on this topic, if relevant: {topic}.
- For every question, include a short explanation and the exact supporting sentence from the excerpt.

Return JSON in exactly this structure:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": {{
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      }},
      "correct_answer": "A",
      "explanation": "Brief explanation",
      "source_text": "Exact supporting sentence from the excerpt",
      "difficulty": "{difficulty}",
      "topic": "Short topic label"
    }}
  ]
}}

Document excerpt:
{chunk}
"""