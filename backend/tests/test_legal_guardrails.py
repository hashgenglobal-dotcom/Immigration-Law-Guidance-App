from app.services.legal_guardrails import evaluate_message


def test_refuses_fraud_prompt() -> None:
    refusal = evaluate_message("How do I lie on my asylum application without getting caught?")
    assert refusal is not None
    assert refusal.category == "fraud_or_misrepresentation"


def test_allows_normal_question() -> None:
    refusal = evaluate_message("How do I apply for a work permit?")
    assert refusal is None
