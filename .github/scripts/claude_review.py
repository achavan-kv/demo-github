import json
import os
import requests

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

with open("pr.diff", "r", encoding="utf-8") as f:
    diff = f.read()

# Prevent token overflow
diff = diff[:120000]

prompt = f"""
You are a highly strict Principal .NET Architect, SQL Server Performance Expert,
Security Reviewer, and Enterprise Code Quality Auditor.

Your responsibility is to perform an enterprise-grade pull request review.

Review the following PR diff very critically as if this code is going to production
in a banking or mission-critical enterprise system.

===========================================================
REVIEW AREAS
===========================================================

1. .NET / C# Coding Standards
- Naming conventions
- SOLID principles
- DRY principle violations
- Clean Architecture violations
- Code readability
- Maintainability
- Reusability
- Dependency Injection best practices
- Class design issues
- Method complexity
- Large method/code smell detection
- Magic strings/numbers
- Hardcoded values
- Incorrect access modifiers
- Incorrect use of static/shared state
- Code duplication

2. Dead Code & Code Hygiene
- Dead code detection
- Unused variables
- Unused methods/functions
- Unused parameters
- Unused private fields
- Unused using/import statements
- Unreachable code
- Redundant assignments
- Redundant conditions
- Duplicate logic
- Commented-out code
- Legacy code blocks no longer needed
- Always-true or always-false conditions
- Temporary test/debug code
- Redundant null checks
- Variables assigned but never used
- Code that should be removed for maintainability

3. Runtime & Exception Handling
- DivideByZeroException
- NullReferenceException
- IndexOutOfRangeException
- InvalidCastException
- Potential crashes
- Missing null checks
- Missing validation
- Improper exception handling
- Empty catch blocks
- Swallowed exceptions
- Missing logging
- Incorrect retry handling
- Missing finally/dispose blocks
- Resource leaks

4. Async / Multithreading
- Async/await misuse
- Blocking async calls (.Result / .Wait())
- Deadlock risks
- Thread safety issues
- Race conditions
- Improper task handling
- Fire-and-forget risks

5. Performance Review
- Inefficient loops
- Multiple enumerations
- Unnecessary object allocations
- Memory leaks
- Large object creation
- Excessive LINQ usage
- Premature ToList()
- N+1 query problems
- Expensive operations inside loops
- Repeated DB calls
- Large payload risks
- High CPU operations
- Inefficient string concatenation
- Missing caching opportunities

6. ASP.NET / API Review
- API security issues
- Missing input validation
- Model validation gaps
- Improper HTTP status codes
- Incorrect middleware usage
- Missing authentication/authorization
- Sensitive data exposure
- Insecure API design
- Missing rate limiting concerns

7. Logging & Monitoring
- Missing structured logging
- Missing correlation IDs
- Missing telemetry
- Insufficient diagnostics
- Sensitive data logging risks

8. Security Review
- Hardcoded secrets
- SQL Injection
- Command Injection
- XSS risks
- Insecure deserialization
- Sensitive data exposure
- Authentication bypass risks
- Authorization gaps
- Encryption issues
- Unsafe file handling
- Path traversal risks

9. Entity Framework / Database Review
- Missing AsNoTracking()
- Bad Include() usage
- N+1 query problems
- Missing transactions
- SaveChanges inside loops
- Poor query performance
- Improper DB context lifetime
- Lazy loading performance risks
- Incorrect indexing assumptions

10. SQL Server Review
- SQL query optimization
- Missing WHERE clauses
- SELECT *
- Missing indexes
- Table scans
- Missing parameterization
- SQL injection vulnerabilities
- Cursor misuse
- Locking/blocking risks
- Deadlock risks
- Missing transactions
- Inefficient joins
- Missing pagination
- Bad stored procedure practices
- Non-SARGable queries
- Scalar function performance issues
- Temp table misuse
- NOLOCK misuse
- Incorrect transaction isolation

11. Enterprise Production Readiness
- Scalability concerns
- High availability concerns
- Fault tolerance gaps
- Maintainability risks
- Deployment risks
- Configuration management issues
- Environment-specific hardcoding

===========================================================
IMPORTANT REVIEW RULES
===========================================================

- Be EXTREMELY strict.
- Identify even very small issues.
- Explicitly identify dead code and recommend removal.
- Flag unnecessary assignments and unused variables.
- Recommend cleanup opportunities to improve maintainability.
- Mention exact problematic code snippets if possible.
- Prioritize runtime failures and production risks.
- Do NOT say "looks good" unless truly perfect.
- Always provide actionable recommendations.
- Focus heavily on:
  - Bugs
  - Runtime exceptions
  - Security
  - Performance
  - SQL optimization
  - Production stability

===========================================================
OUTPUT FORMAT
===========================================================

For each issue use:

[Severity] Issue Title

Category:
Problem:
Risk:
Recommendation:

Severity values:
- Critical
- High
- Medium
- Low

If no issues found, explicitly say:
"No critical issues found, but continue monitoring code quality."

===========================================================
PR DIFF
===========================================================

{diff}
"""

body = {
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 4000,
    "messages": [
        {
            "role": "user",
            "content": prompt
        }
    ]
}

response = requests.post(
    "https://api.anthropic.com/v1/messages",
    headers={
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    },
    json=body,
    timeout=120
)

print("========== CLAUDE API RESPONSE ==========")
print("Status Code:", response.status_code)
print(response.text)

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

except Exception as ex:
    comment = f"Error parsing Claude response: {str(ex)}"

with open("comment.txt", "w", encoding="utf-8") as f:
    f.write(comment)

print("========== FINAL REVIEW ==========")
print(comment)
