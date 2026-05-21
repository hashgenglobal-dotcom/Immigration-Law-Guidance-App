# Legal Review Process (Post-MVP)

**Purpose:** Repeatable attorney review of disclaimers, refusals, and sample answers before production.

## Roles

| Role | Responsibility |
|------|----------------|
| Product owner | Schedules review, tracks sign-off |
| Immigration attorney (external) | Reviews disclaimer text, high-risk routing, sample outputs |
| Engineering | Implements approved text only; does not change legal meaning without review |

## Cadence

- **Before production launch:** Full review (disclaimer, user privacy summary, guardrail refusals).
- **After material changes:** Re-review within 5 business days of merge to `main`.
- **Quarterly:** Re-run sample question set (`docs/legal-review-sample-questions.md`).

## Review checklist

- [ ] Disclaimer states information-only, not advice, no attorney-client relationship
- [ ] High-risk topics route to attorney consultation language
- [ ] Fraud / misrepresentation prompts are refused (see `legal_guardrails.py`)
- [ ] No guarantee language in eligibility explanations
- [ ] Privacy summary matches technical policy
- [ ] Citations are framed as official sources, not firm opinions

## Sign-off template

```
Review date: ___________
Reviewer: ___________
Scope: [ ] Launch  [ ] Quarterly  [ ] Change request #___
Approved: [ ] Yes  [ ] No — notes: ___________
```

## Change control

1. Open PR with label `legal-review-required`.
2. Attach diff of user-visible strings and sample answers.
3. Attorney sign-off recorded in PR comment or linked doc.
4. Merge only after approval.
