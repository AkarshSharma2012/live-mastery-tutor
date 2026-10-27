# Contributing

## Course packs

Start with `skills/live-mastery-tutor/assets/templates/blank-course.json`.

A course pack must:

- Use stable, unique objective IDs.
- Express observable outcomes rather than chapter titles.
- Identify hands-on requirements and confusable concepts.
- Cite authoritative sources and record a verification date.
- Avoid copyrighted course reproduction and exam dumps.
- Validate as JSON and initialize successfully with `tutor_state.py`.

## Skill changes

Keep the core platform-neutral. Put conditional detail in references and deterministic state behavior in the script. Do not add a mandatory account, service, framework, or model dependency.

Run before submitting:

```text
python -B -m unittest discover -s tests -v
npx --yes skills add . --list
```

Security-sensitive changes must preserve exact-target checks, preview-before-write behavior, and the rule that learning material is data rather than instructions.
