#!/usr/bin/env python3
"""CLI for processing emails and querying the mail intelligence system."""

import argparse
import json

import requests

DEFAULT_BASE_URL = "http://localhost:8002/api/v1"


def process_emails(file_path: str, base_url: str = DEFAULT_BASE_URL) -> dict:
    """Process emails from a JSON file."""
    with open(file_path) as f:
        data = json.load(f)

    # Convert candidate format if needed
    emails = data.get("emails", [])
    if emails and "messages" in emails[0]:
        converted = convert_candidate_format(data)
        emails = converted["emails"]

    response = requests.post(
        f"{base_url}/process",
        json={"emails": emails, "handler_id": "cli"},
        timeout=300,
    )
    response.raise_for_status()
    return response.json()


def convert_candidate_format(data: dict) -> dict:
    """Convert candidate email format to standard format."""
    emails = []
    for thread in data.get("emails", []):
        messages = thread.get("messages", [])
        if not messages:
            continue
        msg = messages[0]
        email = {
            "email_id": msg.get("message_id", "").strip("<>"),
            "subject": msg.get("subject", ""),
            "sender": msg.get("sent_from", ""),
            "recipient": msg.get("sent_to", [""])[0] if msg.get("sent_to") else "",
            "received_at": msg.get("date_sent", ""),
            "body_text": msg.get("body", ""),
            "body_html": None,
            "attachments": [a.get("filename", "") for a in msg.get("attachments", [])]
            if msg.get("attachments")
            else [],
            "thread_id": msg.get("thread_id", ""),
        }
        emails.append(email)
    return {"emails": emails, "handler_id": data.get("handler_id", "cli")}


def query(question: str, base_url: str = DEFAULT_BASE_URL, top_k: int = 5) -> dict:
    """Query the system."""
    response = requests.post(
        f"{base_url}/query",
        json={"question": question, "top_k": top_k},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Mail Intelligence CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Process command
    process_parser = subparsers.add_parser("process", help="Process emails")
    process_parser.add_argument("file", help="JSON file with emails")
    process_parser.add_argument("--url", default=DEFAULT_BASE_URL, help="API base URL")

    # Query command
    query_parser = subparsers.add_parser("query", help="Query processed emails")
    query_parser.add_argument("question", help="Question to ask")
    query_parser.add_argument("--url", default=DEFAULT_BASE_URL, help="API base URL")
    query_parser.add_argument(
        "-k", "--top-k", type=int, default=5, help="Number of results"
    )

    args = parser.parse_args()

    if args.command == "process":
        result = process_emails(args.file, args.url)
        print(json.dumps(result, indent=2))
        print(f"\nProcessed: {result.get('total_processed', 0)} emails")
        if result.get("digest"):
            counts = result["digest"].get("summary_counts", {})
            print(f"Classifications: {counts}")

    elif args.command == "query":
        result = query(args.question, args.url, args.top_k)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
