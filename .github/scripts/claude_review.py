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
diff = diff[:150000]

# ==========================================
# PROMPT
# ==========================================

prompt = f"""
You are a highly strict Principal .NET Architect,
SQL Server Performance Expert,
Security Reviewer,
and Enterprise Code Quality Auditor.

Your responsibility is to perform an enterprise-grade pull request review.

Review this PR diff critically as if it is production banking software.

Focus on:

1. .NET / C# standards
2. SOLID principles
3. Runtime bugs
4. Security vulnerabilities
5. SQL optimization
6. Performance issues
7. Async/threading issues
8. Dead code
9. Maintainability
10. Enterprise production risks

Be extremely strict.

Always provide:
- Severity
- Problem
- Risk
- Recommendation

Severity values:
- Critical
- High
- Medium
- Low

===========================================================
PR DIFF
===========================================================

{diff}
"""

# ==========================================
# REQUEST BODY
# ==========================================

body = {
    "model": "claude-sonnet-4-6",
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
# CALL API
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

        if response.status_code == 429:

            print("Rate limit exceeded. Waiting 60 seconds...")
            time.sleep(60)
            continue

        if response.status_code != 200:

            print(response.text)

            with open("comment.txt", "w", encoding="utf-8") as f:
                f.write(
                    f"Claude API Error: {response.status_code}\n\n{response.text}"
                )

            exit(1)

        data = response.json()

        comment = "No review generated."

        if "content" in data:

            parts = []

            for item in data["content"]:

                if item.get("type") == "text":
                    parts.append(item.get("text", ""))

            comment = "\n".join(parts)

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
