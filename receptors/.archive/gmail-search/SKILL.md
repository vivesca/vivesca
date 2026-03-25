---
name: gmail-search
description: Search Gmail for emails matching specific criteria. Use when the user wants to find emails by keyword, sender, subject, or date range.
---

# Gmail Search

Search Gmail for emails using the Gmail API. Useful for finding job rejections, application confirmations, or any email by keyword.

## When to Use

Use this skill when the user:
- Wants to search their Gmail for specific emails
- Needs to find rejection emails and their dates
- Wants to search by sender, subject, or keywords
- Needs to list emails matching certain criteria

## Prerequisites

### First-time Setup

1. **Google Cloud Project with Gmail API enabled**
   - Go to https://console.cloud.google.com
   - Create a project or use existing one
   - Enable Gmail API
   - Configure OAuth consent screen (External, Testing mode)
   - Create OAuth credentials (Desktop app)
   - Add your email as a test user

2. **Credentials file**
   - Download `credentials.json` from Google Cloud Console
   - Place it in `/Users/terry/notes/scripts/credentials.json`

See [[Gmail API Setup]] for detailed setup instructions.

## Instructions

### Step 1: Run the Search Script

```bash
cd /Users/terry/notes/scripts
uv run gmail_rejection_search.py
```

On first run, a browser will open for OAuth authorization. After authorizing, a `token.pickle` file is saved for future runs.

### Step 2: Interpret Results

The script searches for common rejection email patterns:
- "unfortunately application"
- "regret to inform"
- "not moving forward"
- "position has been filled"
- etc.

Results are sorted by date (newest first) showing:
- Date
- Sender
- Subject line

### Custom Searches

To search for different criteria, modify the `rejection_queries` list in the script or create a new script using the same authentication:

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-auth-oauthlib",
#     "google-auth-httplib2",
#     "google-api-python-client",
# ]
# ///

from gmail_rejection_search import get_gmail_service

service = get_gmail_service()

# Custom search query (Gmail search syntax)
results = service.users().messages().list(
    userId='me',
    q='from:linkedin.com subject:application',
    maxResults=20
).execute()

messages = results.get('messages', [])
for msg in messages:
    # Process messages...
    pass
```

## Modifying Emails

The script now supports marking emails as read and archiving:

```python
from gmail_rejection_search import get_gmail_service, mark_as_read, archive_email, mark_read_and_archive

service = get_gmail_service()

# Mark a single email as read
mark_as_read(service, msg_id)

# Archive a single email (remove from inbox)
archive_email(service, msg_id)

# Mark as read AND archive in one call
mark_read_and_archive(service, msg_id)

# Bulk operation example
results = service.users().messages().list(
    userId='me',
    q='from:railway.app subject:failed',
    maxResults=20
).execute()
for msg in results.get('messages', []):
    mark_read_and_archive(service, msg['id'])
```

**Note**: After updating scope from `gmail.readonly` to `gmail.modify`, delete `token.pickle` and re-authenticate.

## Gmail Search Syntax

Use Gmail's search operators in queries:
- `from:sender@email.com` - From specific sender
- `to:recipient@email.com` - To specific recipient
- `subject:keyword` - In subject line
- `"exact phrase"` - Exact phrase match
- `after:2024/01/01` - After date
- `before:2024/12/31` - Before date
- `has:attachment` - Has attachments
- `label:inbox` - Specific label

Combine with AND (space) or OR:
- `from:linkedin.com subject:application`
- `from:company.com OR from:recruiter.com`

## Files

- Script: `/Users/terry/notes/scripts/gmail_rejection_search.py`
- Credentials: `/Users/terry/notes/scripts/credentials.json`
- Token: `/Users/terry/notes/scripts/token.pickle` (created after first auth)
- Setup notes: [[Gmail API Setup]]

## Troubleshooting

**"credentials.json not found"**
- Download from Google Cloud Console → Clients → Desktop client 1

**"Access blocked" or auth error**
- Ensure your email is added as a test user in OAuth consent screen
- Delete `token.pickle` and re-authorize

**"Insufficient Permission" when modifying emails**
- The token was created with read-only scope
- Delete `token.pickle` and re-run to get new token with modify scope

**No results found**
- Try broader search terms
- Check if emails exist in your inbox with those keywords

**Token expired**
- Delete `token.pickle`, re-run to trigger OAuth flow

## Safety Notes

- Never delete emails programmatically without explicit user confirmation
- Be careful with bulk operations — always preview results first
- Sensitive data: results may contain personal information, don't log to shared locations
