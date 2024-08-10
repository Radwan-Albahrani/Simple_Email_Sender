# Simple Email Sender

This is a simple email sender that uses the smtplib library to send emails. It is a simple script that can be used to send emails to multiple recipients. The script is written in Python and uses the smtplib library to send emails. The script takes the following inputs:

## Setup

### Environment Variables

- `LOGIN_EMAIL` - The email address from which the email will be sent.
- `LOGIN_PASSWORD` - The password for the email address from which the email will be sent.
- `EMAIL_PATHS` - Split into multiple parts
  - `EMAIL_PATHS_STARTUPS_PATH` - The path to the file containing the email addresses of the Startups.
  - `EMAIL_PATHS_FULL_PATH` - The path to the file containing the email addresses of the of all emails.
  - `EMAIL_PATHS_TEST_PATH` - The path to the file containing the email addresses of the test emails.
- `EMAIl_BASE` - Split into Multiple Parts
  - `EMAIL_BASE_SUBJECT` - The subject of the email.
  - `EMAIL_BASE_TEMPLATE` - The body of the email.
  - `EMAIL_BASE_ATTACHMENT_PATH` - The path to the attachment file.
  - `EMAIL_BASE_SENDER_NAME` - The name of the sender.
  - `EMAIL_BASE_SENDER_EMAIL` - The email address of the sender.
- `GEMINI_API` - Split into Multiple Parts
  - `GEMINI_API_KEY` - The API key for the Gemini API.
  - `GEMINI_API_RESUME_TEXT` - The API secret for the Gemini API.
  - `GEMINI_API_EMAIL_TEMPLATE` - The URL for the Gemini API.

### Running the Script
