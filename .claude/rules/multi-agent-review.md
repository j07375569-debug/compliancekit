# Multi-Agent Review Pattern

## Principle
The agent that writes code NEVER reviews its own code. A separate validator agent with a fresh context window must review all non-trivial changes.

## When to Use
- Any change touching >50 lines of code
- Any change to API routes or database schema
- Any security-related change (auth, CORS, secrets)
- Any change to payment/billing logic
- Before any deploy to production

## Builder Agent
- Has full read/write access
- Writes code, runs tests, iterates
- Documents what was changed and why in session_log.md

## Validator Agent
- Spawned as a SEPARATE agent with fresh context
- READ-ONLY scope — cannot modify files
- Reviews the diff, not the whole codebase
- Checks for:
  1. Logic errors and edge cases
  2. Security vulnerabilities (injection, XSS, CSRF)
  3. Missing error handling
  4. Broken API contracts
  5. Design rule violations (reference rules/design.md)
  6. Performance issues (N+1 queries, unbounded loops)

## Execution Pattern
```
1. Builder agent completes work
2. Builder creates a summary of changes
3. Spawn validator agent with:
   - The diff or changed files
   - Relevant rule files from .claude/rules/
   - Instruction: "Find bugs, security holes, and design violations. Do NOT modify files."
4. Validator returns findings
5. Builder addresses findings
6. If findings were critical → re-validate with fresh validator
```

## In Claude Code / Cowork
Use the Agent tool with a prompt like:
"You are a code validator. Review the following files for bugs, security issues, and design violations. You may NOT modify any files. List every issue you find with file, line, and severity."
