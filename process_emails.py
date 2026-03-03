#!/usr/bin/env python3
import json

data = json.load(open("emails_candidate.json"))
emails = data["emails"]
processed = []

for email in emails:
    messages = email.get("messages", [])
    if messages:
        msg = messages[0]
        attachments = msg.get("attachments", [])
        processed.append(
            {
                "email_id": email.get("thread_id", "unknown"),
                "subject": msg.get("subject", "No Subject"),
                "sender": msg.get("sent_from", "unknown@example.com"),
                "recipient": ", ".join(msg.get("sent_to", [])),
                "received_at": msg.get("date_sent", "2024-01-01T00:00:00Z"),
                "body_text": msg.get("body", ""),
                "body_html": None,
                "attachments": [a.get("filename") for a in attachments]
                if attachments
                else [],
                "thread_id": email.get("thread_id", ""),
            }
        )

print(f"Processed {len(processed)} emails")

output = {"emails": processed}
with open("emails_simple.json", "w") as f:
    json.dump(output, f, indent=2)

print("Written to emails_simple.json")
