# Simple Email Sender

Sends personalised job-application emails to a list of recipients over Gmail
SMTP. Email bodies are generated with the Gemini API from your résumé plus
context about each company gathered from a local
[SearXNG](https://docs.searxng.org/) instance. Recipients on a blacklist file
are skipped, and duplicates across lists are removed automatically.

## Requirements

- Python 3.12
- Docker — only if you want LLM-personalised bodies (runs the SearXNG instance)
- A Gmail account with an [App Password](https://myaccount.google.com/apppasswords)
- A [Gemini API key](https://aistudio.google.com/apikey)

## Setup

### 1. Virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt` holds the direct dependencies. `requirements.lock.txt` is a
full `pip freeze` of a known-good environment. `requirements-dev.txt` adds the
lint and type-check tools.

### 2. Environment variables

```bash
cp .env.example .env
```

Only six values are required — everything else is auto-detected:

| Variable | Description |
| --- | --- |
| `LOGIN_EMAIL` | Gmail address used for SMTP |
| `LOGIN_PASSWORD` | Gmail **App Password**, not your account password |
| `GEMINI_API_KEY` | Gemini API key |
| `EMAIL_BASE_SENDER_NAME` | Display name on the `From:` header |
| `EMAIL_BASE_SENDER_EMAIL` | Address on the `From:` header |

Auto-detected, override in `.env` only if the wrong file is picked:

| What | Where it comes from |
| --- | --- |
| Résumé attachment | the single `.pdf` in `assets/attachments/` |
| Résumé text | `assets/attachments/resume_text.txt`, or the single `.txt` there |
| Email template | `assets/templates/email_template.txt` |
| LLM prompt | `assets/templates/gemini_prompt.txt` |
| Fallback body | `assets/templates/default_body.txt` |
| Recipient lists | every list-shaped `.json` under `assets/` |
| Blacklist | `assets/output/blacklist.json` |
| Gemini model | `gemini-3.6-flash` |

See `.env.example` for the full set of override names. `.env` is gitignored —
never commit real credentials.

### 3. Assets

Put your files in place:

```
assets/attachments/Your Name - Resume.pdf    attached to every email
assets/attachments/resume_text.txt           plain text, fed to the LLM
assets/templates/email_template.txt          {name}, {body}, {sender_name}
```

`email_template.txt`, `gemini_prompt.txt` and `default_body.txt` are committed;
the rest of `assets/` is gitignored because it holds personal data.

### 4. SearXNG (only for LLM bodies)

Body generation queries a local SearXNG instance for company context:

```bash
cp searxng/settings.example.yml searxng/settings.yml
# set a real secret_key:  openssl rand -hex 32
docker compose up -d
```

It listens on `http://localhost:8080`, which the default search URL points at.
Keep `json` under `formats:` in `searxng/settings.yml`, or the API returns HTML.
If SearXNG is unreachable the run continues — bodies are just generated without
company context.

### 5. Recipient lists

Any `.json` under `assets/` is offered as a list if it parses as either a plain
array or a TinyDB-style export:

```json
[{ "name": "Example Company", "emails": ["careers@example.com"] }]
```

```json
{ "_default": { "1": { "name": "Example Company", "emails": ["careers@example.com"] } } }
```

Files of any other shape are skipped silently. To build lists from raw scraped
exhibitor data:

```bash
python app/services/response_parser.py --input-dir assets/input --output-dir assets/output
```

## Usage

Run from the repository root — asset paths resolve against the working directory:

```bash
.venv/bin/python app/main.py
```

The script then walks you through:

1. **Pick lists.** Discovered lists are shown numbered, test lists first.
   Select with `1`, several with `1,3`, a range with `1-3`, or `all` / `test`.
   Blank cancels. Picking several merges them, dropping duplicate company names
   and anything on the blacklist.
2. **Choose personalisation.** `y` generates each body with Gemini; `n` uses the
   fallback body from `default_body.txt`.
3. **Choose a starting position**, to resume a run that stopped part-way.
4. **Confirm** by typing `YES` in full.

```
Available recipient lists:
  1) assets/test/emails_cleaned.json                 8 recipients  [test]
  2) assets/output/emails_cleaned.json             380 recipients
  3) assets/input/dammam/medium_company_size.json   87 recipients

Select with numbers (1), several (1,3), a range (1-3), 'all', or 'test'.
Selection (blank to cancel): test
```

Emails go out in batches of 10, 8 threads at a time, pausing between batches
(60s with the LLM, 10s without). Progress and failures are appended to
`logs/email_logs.log`. SMTP failures are retried up to 5 times with a ~1 minute
backoff, and addresses that already went out are never re-sent on a retry.

> Do a `test` run first. Sending is irreversible, and the full list is several
> hundred recipients.

## Development

```bash
pip install -r requirements-dev.txt
ruff check app/     # lint + import order
mypy                # strict type check
pyright             # strict type check
```

## Project layout

```
app/
  main.py                     entry point — discovery, selection, dispatch
  config.py                   pydantic-settings models, path auto-detection
  schemas.py                  RecipientModel, SearXNG response models
  common.py                   Gemini generation, SearXNG lookup, SMTP send
  services/
    email_sender.py           interactive confirmation flow
    recipient_lists.py        list discovery, selection parsing, merging
    response_parser.py        one-off scraped-data cleanup script
assets/
  attachments/                résumé PDF and text
  templates/                  email template, LLM prompt, fallback body
  input/ output/ test/        recipient lists
searxng/                      SearXNG config for docker-compose
logs/                         run logs
```

## Troubleshooting

**`SMTPAuthenticationError: 535 ... BadCredentials`** — the Gmail App Password
was revoked or mistyped. Generate a new one at
<https://myaccount.google.com/apppasswords> and update `LOGIN_PASSWORD`.

**`404 ... model is no longer available`** — Google retired that Gemini model.
Set `GEMINI_API_MODEL` in `.env` to a current one.

**`Search lookup failed`** in the logs — SearXNG isn't running or isn't
returning JSON. The run continues without company context.
