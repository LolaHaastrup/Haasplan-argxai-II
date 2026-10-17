# HaasPlan XAI

**Argumentation-Based Explanations for Collaborative Planning**

Streamlit app for the argumentation-based plan explanation chatbot
(ECR_2024_17, University of Huddersfield).

## Two modes

**Explore** — a plan selector, the plan, and a free dialogue. This is the
demonstration mode. Nothing is recorded. A researcher-only **Framework** tab
(attack and defeat structure and the diagram) appears after the sidebar
password is entered. It is hidden from participants.

**User study** — the six-stage participant flow: information sheet, consent,
briefing, dialogue, questionnaire, debrief.

## Domains

| Key | Domain | Actions | CQ instances |
|-----|--------|---------|--------------|
| `bus_train` | Transport, bus and train journey | 6 | 40 |
| `cash_transfer` | Social protection, cash transfer with grievance resolution | 11 | 73 |

Both plans are valid. Explaining why a plan fails needs argument schemes of
its own and is scoped as later work, so no failing plan appears in the app.

## How the explanation is organised

Interaction runs through the Plan Summary Argument, not through the plan. The
premises of that argument are assumptions that support its conclusion, that the
plan is valid. A premise is challenged by a critical question, and the system
answers the challenge by generating an argument scheme, which has premises and
a conclusion of its own.

The flow is: read the summary argument, pick a premise to challenge, pick one
of its critical questions, pick the action it concerns, and read the scheme
that answers it.

Every answer is written to stand on its own (`presenter.py`). It names the
actions involved, says what a scheme is, spells out each premise and the
conclusion in full, and defines reversing an order where that idea appears.

This is presentation only. The protocol still receives a challenge of one
critical question on one action, so legality, termination and faithfulness are
unchanged. The data files are untouched, and the stored transcript keeps the
framework's own wording, so the analysis does not depend on how text is
phrased on screen.

**Open question for the supervisor.** The app no longer says that a premise
"is" a scheme. It does show that answering a challenge uses a scheme, and some
answers rely on a second scheme (for example S3 answering CQ1 cites S1 as one of
its premises). Whether a premise is itself supplied by a scheme, as well as
being answered by one, should be confirmed at the next meeting.

Both frameworks come from **one** extraction implementation, Module 3b of the
notebook, which reads conditions and effects off the Unified Planning model
rather than matching on action names. That is what the second domain is
evidence for.

### Adding a third domain

1. Add an entry to `REGISTRY` in `domains.py`.
2. Drop `<key>_plan.json`, `<key>_S8_PSA.json`, `<key>_CQ_results.json` and
   `<key>_AF_labels.json` into `data/`. Optionally `<key>_display_names.json`.

No other file changes. The selector picks up any domain whose artefacts exist.

## Running it

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

The `data/` folder already contains both domains, so it runs immediately.

## Deploying

Push to GitHub, create a Streamlit Cloud app pointing at `streamlit_app.py`,
then paste your secrets into the app's Secrets box.

**Storage.** Streamlit Community Cloud has an ephemeral filesystem: it is wiped
on redeploy and after inactivity. The default local store is for development.
Set `sheet_id` and `[gcp_service_account]` in secrets to switch to Google
Sheets. The researcher panel shows which store is active and warns in red when
it is not durable.

**Researcher panel.** Set `admin_password` in secrets. It exposes the domain
assignment for study participants, the storage status, a faithfulness check,
and a response download.

## Before running with participants

`study_config.py` holds every participant-facing string in one file. Text
marked `[REPLACE]` is placeholder scaffolding and needs your approved wording.
`RETENTION_YEARS = 10` is the single source of truth for the retention period
and is interpolated into the information sheet, a consent item and the debrief.

## Layout

| File | Purpose |
|------|---------|
| `streamlit_app.py` | Landing page, explore mode, study flow, researcher panel |
| `domains.py` | Domain registry, the only file a new domain touches |
| `explanation_dialogue.py` | Protocol engine, identical to notebook Module 10b |
| `study_config.py` | All participant-facing text and the questionnaire |
| `storage.py` | Pluggable response storage |
| `data/` | Framework artefacts, both domains |
| `assets/` | University logo, converted from CMYK to RGB |
