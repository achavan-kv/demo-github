import os
import time
import requests
import sys

# ==========================================
# CONFIG
# ==========================================

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

MODEL = "claude-sonnet-4-6"

# Best enterprise balance
MAX_DIFF_SIZE = 40000

MAX_RETRIES = 3

# ==========================================
# LOAD PR DIFF
# ==========================================

with open("pr.diff", "r", encoding="utf-8") as f:
    diff = f.read()

# ==========================================
# SKIP EMPTY REVIEW
# ==========================================

if not diff.strip():

    with open("comment.txt", "w", encoding="utf-8") as f:
        f.write("No .cs or .sql changes detected for review.")

    print("No .cs or .sql changes detected.")
    sys.exit(0)

# ==========================================
# REDUCE TOKEN USAGE
# ==========================================

diff = diff[:MAX_DIFF_SIZE]

# ==========================================
# REVIEW PROMPT
# ==========================================

prompt = f"""
Act as a strict enterprise code reviewer.

Review ONLY for important issues:

- Runtime bugs
- Null reference risks
- SQL issues
- Security vulnerabilities
- Performance problems
- Async/threading issues
- Dead code
- Bad exception handling
- Production risks
- Maintainability concerns
- SOLID/design violations

Rules:
- Be concise
- Ignore cosmetic/style suggestions
- Prioritize production-impacting issues
- Mention exact problematic code when possible
- Do not add decorative titles/headings

Output format:

[Severity] Title

Problem:
Risk:
Recommendation:

Severity:
Critical | High | Medium | Low

PR DIFF:
{diff}
"""

# ==========================================
# REQUEST BODY
# ==========================================

body = {
    "model": MODEL,
    "max_tokens": 1200,
    "temperature": 0,
    "messages": [
        {
            "role": "user",
            "content": prompt
        }
    ]
}

# ==========================================
# CALL CLAUDE API
# ==========================================

for attempt in range(MAX_RETRIES):

    try:

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json=body,
            timeout=180
        )

        print("Status:", response.status_code)

        # ==========================================
        # RATE LIMIT HANDLING
        # ==========================================

        if response.status_code == 429:

            print("Rate limited. Waiting 60 seconds...")
            time.sleep(60)
            continue

        # ==========================================
        # API ERROR HANDLING
        # ==========================================

        if response.status_code != 200:

            error_text = response.text

            print(error_text)

            with open("comment.txt", "w", encoding="utf-8") as f:
                f.write(
                    f"Claude API Error: {response.status_code}\n\n{error_text}"
                )

            sys.exit(1)

        # ==========================================
        # PARSE RESPONSE
        # ==========================================

        data = response.json()

        comment = "No review generated."

        if "content" in data:

            text_parts = []

            for item in data["content"]:

                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))

            comment = "\n".join(text_parts)

        # ==========================================
        # SAVE REVIEW
        # ==========================================

        with open("comment.txt", "w", encoding="utf-8") as f:
            f.write(comment)

        print(comment)

        break

    except Exception as ex:

        if attempt == MAX_RETRIES - 1:

            with open("comment.txt", "w", encoding="utf-8") as f:
                f.write(f"Review Failed:\n\n{str(ex)}")

            raise ex

        print("Retrying...")
        time.sleep(30)
