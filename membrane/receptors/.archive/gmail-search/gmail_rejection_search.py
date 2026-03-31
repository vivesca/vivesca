#!/usr/bin/env python3

from __future__ import annotations

# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-auth-oauthlib",
#     "google-auth-httplib2",
#     "google-api-python-client",
# ]
# ///
"""
Search Gmail for job rejection emails and extract dates.

Usage:
    uv run gmail_rejection_search.py

First run:
1. Download credentials.json from Google Cloud Console
2. Place it in the same directory as this script
3. Run: uv run gmail_rejection_search.py
4. A browser will open for authorization (first time only)
"""

import pickle
from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying scopes, delete token.pickle
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Directory where this script lives
SCRIPT_DIR = Path(__file__).parent


def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None
    token_path = SCRIPT_DIR / "token.pickle"
    credentials_path = SCRIPT_DIR / "credentials.json"

    # Load existing token
    if token_path.exists():
        with open(token_path, "rb") as token:
            creds = pickle.load(token)

    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                print(f"ERROR: credentials.json not found at {credentials_path}")
                print("Download it from Google Cloud Console -> Clients -> Desktop client 1")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token for next run
        with open(token_path, "wb") as token:
            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)


def search_rejection_emails(service, max_results=50):
    """Search for job rejection emails."""

    # Common rejection phrases in subject or body
    rejection_queries = [
        "subject:(unfortunately application)",
        "subject:(regret to inform)",
        "subject:(not moving forward)",
        "subject:(unsuccessful application)",
        "subject:(application status)",
        "subject:(thank you for your interest) -interview",
        '"we have decided to move forward with other candidates"',
        '"unfortunately we will not be moving forward"',
        '"regret to inform you"',
        '"not selected for"',
        '"decided not to proceed"',
        '"position has been filled"',
    ]

    all_messages = []
    seen_ids = set()

    print("Searching for rejection emails...")

    for query in rejection_queries:
        try:
            results = (
                service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )

            messages = results.get("messages", [])
            for msg in messages:
                if msg["id"] not in seen_ids:
                    seen_ids.add(msg["id"])
                    all_messages.append(msg)
        except Exception as e:
            print(f"  Query failed: {query[:50]}... - {e}")

    print(f"Found {len(all_messages)} potential rejection emails\n")
    return all_messages


def get_email_details(service, msg_id):
    """Get email date, subject, and sender."""
    msg = (
        service.users()
        .messages()
        .get(
            userId="me", id=msg_id, format="metadata", metadataHeaders=["Date", "Subject", "From"]
        )
        .execute()
    )

    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}

    # Parse date
    date_str = headers.get("Date", "")
    try:
        # Handle various date formats
        for fmt in [
            "%a, %d %b %Y %H:%M:%S %z",
            "%d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
        ]:
            try:
                date = datetime.strptime(date_str.split(" (")[0].strip(), fmt)
                break
            except ValueError:
                continue
        else:
            date = None
    except Exception:
        date = None

    return {
        "id": msg_id,
        "date": date,
        "date_str": date_str,
        "subject": headers.get("Subject", "(no subject)"),
        "from": headers.get("From", "(unknown)"),
    }


def main():
    print("=" * 60)
    print("Gmail Rejection Email Search")
    print("=" * 60 + "\n")

    service = get_gmail_service()
    if not service:
        return

    messages = search_rejection_emails(service)

    if not messages:
        print("No rejection emails found.")
        return

    # Get details for each message
    emails = []
    print("Fetching email details...")
    for i, msg in enumerate(messages):
        if i % 10 == 0:
            print(f"  Processing {i + 1}/{len(messages)}...")
        details = get_email_details(service, msg["id"])
        emails.append(details)

    # Sort by date (newest first)
    emails.sort(key=lambda x: x["date"] or datetime.min, reverse=True)

    # Display results
    print("\n" + "=" * 60)
    print("REJECTION EMAILS (sorted by date, newest first)")
    print("=" * 60 + "\n")

    for email in emails:
        date_display = email["date"].strftime("%Y-%m-%d") if email["date"] else "Unknown date"
        sender = email["from"]
        # Truncate sender if too long
        if len(sender) > 40:
            sender = sender[:37] + "..."
        subject = email["subject"]
        if len(subject) > 50:
            subject = subject[:47] + "..."

        print(f"{date_display}  |  {sender}")
        print(f"             {subject}")
        print()

    # Summary
    print("=" * 60)
    print(f"Total: {len(emails)} rejection emails found")
    if emails and emails[-1]["date"]:
        print(f"Earliest: {emails[-1]['date'].strftime('%Y-%m-%d')}")
    if emails and emails[0]["date"]:
        print(f"Latest:   {emails[0]['date'].strftime('%Y-%m-%d')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
