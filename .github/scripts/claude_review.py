import os
import time
import requests

# ==========================================
# API KEY
# ==========================================

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# ==========================================
# LOAD DIFF
# ==========================================

with open("pr.diff", "r", encoding="utf-8") as f:
    diff = f.read()

# Prevent token overflow
diff = diff[:100000]

# ==========================================
# PROMPT
# ==========================================

prompt = f"""
You are a highly strict Principal .NET Architect, SQL Server Performance Expert,
Security Reviewer, and Enterprise Code Quality Auditor.

Review this pull request very critically for:
- Bugs
- Runtime failures
- Security vulnerabilities
- SQL performance issues
- .NET architecture issues
- Dead code
- Maintainability
- Performance problems
- Async/threading issues
- Enterprise production risks

Provide actionable recommendations.

Use this format:

[Severity] Issue Title

Category:
Problem:
Risk:
Recommendation:

Severity:
- Critical
- High
- Medium
- Low

PR DIFF:

{diff}
"""

# ==========================================
# REQUEST BODY
# ==========================================

body = {
    "model": "claude-3-haiku-20240307",
    "max_tokens": 4000,
    "temperature": 0.1,
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

max_retries = 3

for attempt in range(max_retries):

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

        print("========== CLAUDE API RESPONSE ==========")
        print("Status Code:", response.status_code)
        print(response.text)

        # Rate limit handling
        if response.status_code == 429:

            print("Rate limit exceeded. Waiting 60 seconds...")
            time.sleep(60)
            continue

        # Error handling
        if response.status_code != 200:

            with open("comment.txt", "w", encoding="utf-8") as f:
                f.write(
                    f"Claude API Error: {response.status_code}\n\n{response.text}"
                )

            exit(1)

        data = response.json()

        comment = "No review generated."

        try:

            if "content" in data:

                parts = []

                for item in data["content"]:

                    if item.get("type") == "text":
                        parts.append(item.get("text", ""))

                comment = "\n".join(parts)

        except Exception as parse_error:

            comment = f"Error parsing Claude response:\n\n{str(parse_error)}"

        # Save comment
        with open("comment.txt", "w", encoding="utf-8") as f:
            f.write(comment)

        print("========== FINAL REVIEW ==========")
        print(comment)

        break

    except Exception as ex:

        if attempt == max_retries - 1:

            with open("comment.txt", "w", encoding="utf-8") as f:
                f.write(f"Claude Review Failed:\n\n{str(ex)}")

            raise ex

        print("Retrying after error...")
        time.sleep(30)
