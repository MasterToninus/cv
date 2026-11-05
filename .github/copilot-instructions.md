# Copilot instructions

<!-- BEGIN USER COMMIT PROVENANCE POLICY -->
## Commit provenance policy — 17 October 2026

Apply this convention whenever you create or propose a new commit message for this user's repositories:

- Start the subject with `[AI] ` for predominantly AI-generated content (approximately 90% AI).
- Start the subject with `[AI-Human] ` for content developed interactively by the human and an AI.
- Use no provenance tag only for content classified as human-authored. Never omit the tag to present AI-generated or AI-assisted changes as human-only.

Use exactly these capitalizations and put the tag before any existing conventional-commit prefix, for example `[AI-Human] docs: revise the AI policy`. Classify the origin of the committed changes, not the account running Git. A prompt or approval alone does not turn predominantly AI-generated content into human-authored content. State uncertainty rather than inventing an exact percentage or silently claiming human provenance.

Check the subject before committing and retain the appropriate tag in any newly authored squash or merge message. Pass this convention to delegated agents and commit-message generators. When initializing a new repository for this user, carry this policy into its agent instructions.

This prospective rule supersedes older tag spellings; preserve historical commit messages and records. Continue to respect the current task's scope and existing commit/push permissions. This labeling policy does not itself require a commit or push.
<!-- END USER COMMIT PROVENANCE POLICY -->

## Commit messages and documentation

Write all new or proposed commit subjects and bodies in English, including newly authored squash and merge messages. Preserve the required `[AI]` or `[AI-Human]` provenance prefix and pass this rule to delegated agents. Do not rewrite historical commits to translate them. See the [commit-language policy](../AGENTS.md#commit-message-language).

Keep public documentation in English, with concise folder READMEs and working links. Keep the `.github/` folder guide in `GUIDE.md` so the root README remains the repository landing page. Operational instructions belong in the [build guide](../docs/build.md); follow the [public-documentation policy](../AGENTS.md#public-documentation).

## CV tailoring workflow

For every request to tailor a CV to a position, read and follow the mandatory
workflow in [AGENTS.md](../AGENTS.md#tailoring-a-cv-for-a-position). Validate
`getactivities` and YAML loading, regenerate the CV, then adapt a copy of the
newly generated TeX in `ai-tailored/`.

Use the [AI filename and version convention](../AGENTS.md#ai-document-filenames-and-versions)
for those sources, and preserve useful review notes under `docs/ai-tailored/`.

Before generating a CV for tailoring, verify the entire shared BibTeX file using the [primary-source metadata checklist](../AGENTS.md#bibliography-metadata-checks), including authors, identifiers, publication details, and current manuscript status. Record sources, verification date, and unresolved conflicts.
