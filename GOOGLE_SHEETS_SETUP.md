# Getting responses into a Google Sheet

One row per participant, one column per questionnaire item, Likert coded 1 to
5. Download as CSV and it loads straight into R, SPSS, Stata or pandas.

## What the sheet looks like

38 columns, in this order:

| Group | Columns |
|-------|---------|
| Session | `timestamp`, `participant_code`, `domain`, `workflow`, `verdict_shown`, `consent_version`, `retention_years` |
| Behaviour, from the transcript | `cqs_available`, `cqs_challenged_observed`, `premises_grounded`, `nodes_understood`, `explainee_moves`, `move_bound`, `closed_by_user`, `seconds_on_dialogue`, `conceded_cqs` |
| Agreement with the explanation | `verdict_agreement`, `verdict_reason` |
| Derived at save time | `drill_down_moves`, `distinct_cq_types`, `closed_deliberately`, `cq_sequence` |
| Likert, coded 1 to 5 | `C1` `C2` `C3` `PC1` `PC2` `K1` `K2` `T1` `T2` `SAT1` `SAT2` `AA` |
| Open text | `OQ1` `OQ2` `OQ3` |
| Archive | `transcript_compact` |

Coding: 1 Strongly disagree, 2 Disagree, 3 Neutral, 4 Agree, 5 Strongly agree.

Column names `verdict_shown`, `verdict_agreement` and `verdict_reason` are kept
from earlier versions so the analysis script keeps working. On screen the
participant sees "explanation" instead of "verdict". `verdict_agreement` holds
"I agree with the explanation", "I do not agree with the explanation" or "I am
not sure". Rows collected before this change hold the older "accept the
verdict" wording; the analysis script reads both.

`cqs_challenged_observed` is the true number of critical questions clicked,
taken from the transcript. The self-reported count (`DL`) and the failure items
(`F1`, `F2`) are no longer collected.

**If the sheet already has a header row from an earlier version, clear the
whole sheet, header included, before redeploying.** The app writes the header
itself when the sheet is empty.

## Setting it up

### 1. Create the sheet

Create a blank Google Sheet. Do not add headers; the app writes them on the
first response. From its URL, copy the id:

```
https://docs.google.com/spreadsheets/d/THIS_LONG_STRING_IS_THE_ID/edit
```

### 2. Create a service account

1. Go to `console.cloud.google.com` and create a project, or pick an existing one.
2. **APIs & Services → Library**. Enable **Google Sheets API**, then enable
   **Google Drive API**.
3. **APIs & Services → Credentials → Create credentials → Service account**.
   Give it any name. No roles are needed.
4. Open the service account, go to **Keys → Add key → Create new key → JSON**.
   A JSON file downloads. This is the only copy; Google will not show it again.

### 3. Share the sheet with the service account

Open the JSON file and find `client_email`. It looks like
`something@your-project.iam.gserviceaccount.com`.

In your Google Sheet, click **Share**, paste that address, give it **Editor**,
and untick "Notify people". The sheet will not work if you skip this step: the
service account is a separate identity from your own Google account.

### 4. Put the credentials in Streamlit secrets

In your deployed app, open **Settings → Secrets** and paste this, filling the
values from the downloaded JSON:

```toml
admin_password = "a-long-random-string"
sheet_id = "the-id-from-the-sheet-url"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\nMIIE...\n-----END PRIVATE KEY-----\n"
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
token_uri = "https://oauth2.googleapis.com/token"
```

**The `private_key` is the step people get wrong.** In the JSON file the key
contains literal `\n` sequences. Keep them exactly as they are, on one line,
inside double quotes. Do not paste the key across multiple real lines.

Save. The app restarts by itself.

### 5. Verify before recruiting

Open the app, enter your `admin_password` in the sidebar. You should see:

```
Storage: Google Sheet
Sheet connected, 0 response row(s), header not yet written
```

If instead it says the store is not durable, the secrets were not read. If it
says the sheet is unreachable, either the id is wrong or you did not share the
sheet with the `client_email`.

Then run one pass through the study yourself and confirm a row appears.

## Every save is written twice

Each response goes to the sheet and to a local `responses_backup.jsonl`. If the
Sheets call fails, the app tells the participant it saved and records where, so
the response is not lost outright. The local file does not survive a container
restart on Streamlit Cloud, so it is a safety net rather than a store.

The researcher panel has CSV and JSON download buttons that read from whichever
backend is live.

## Rate limits

Google allows roughly 60 write requests per minute per user. Each participant
is one append, so this only matters if dozens of people submit in the same
minute. Worth knowing if you post the link to a large LinkedIn audience at once.
