# Context Engineering Rules (Manus-Derived)

## 1. File System as External Memory

The file system is unlimited context. Use it.

- **Raw data → files.** Search results, API responses, scraped content, logs — write them to files immediately. Don't hold them in the conversation.
- **Summaries → context.** Only keep 1-2 sentence conclusions in working memory. The file path is your retrieval key.
- **Pattern:** `save raw → summarize → keep summary + path → drop raw from context`

Example:
```
BAD:  Read entire 2000-line app.py into context, analyze it there
GOOD: Read app.py, write findings to .claude/scratch/app-analysis.md, keep summary
```

## 2. KV-Cache Optimization

These rules reduce token cost by 10x when using Claude API (cached: $0.30/MTok vs uncached: $3/MTok).

- **Stable prefixes.** The top of claude.md and all rule files must NOT contain timestamps, counters, or volatile data. Static content first, dynamic content last.
- **Append-only.** Never edit previous conversation entries. Only append new information.
- **Deterministic serialization.** When writing JSON to files, use sorted keys and consistent formatting. Random key order = cache miss.
- **Don't restructure mid-session.** If you need to reorganize a file, do it at session boundaries, not mid-task.

## 3. Todo.md as Attention Anchor

This is the most underrated pattern from Manus. The todo list isn't just tracking — it's a cognitive steering mechanism.

- **Recite the plan at each iteration.** Before choosing your next action, re-read todo.md. This refocuses attention on the actual goal and prevents drift.
- **Check off completed items in-place.** `- [ ]` → `- [x]`. Don't delete completed items until session ends.
- **Add discovered subtasks immediately.** If you find a new blocker or subtask, add it to todo.md before continuing work.

## 4. Restorable Context Compression

When context gets long, compress aggressively — but keep restoration keys.

| Content Type | Keep | Drop |
|-------------|------|------|
| Web page content | URL | Full HTML/text |
| File contents | File path | Raw content |
| API responses | Endpoint + summary | Full JSON body |
| Error traces | Error message + file:line | Full stack trace |
| Search results | Top 3 URLs + one-liner each | Full snippets |

Rule: If you can `cat` it or `curl` it again, you don't need it in context.

## 5. Tool State Awareness

Don't thrash between unrelated tools. Group related operations.

```
BAD:  read file → search web → edit file → search web → read another file
GOOD: read all needed files → plan → execute edits → validate
```

## 6. Structured Variation (Anti-Pattern Breaking)

When Claude gets stuck in a loop or produces repetitive output:
- Rephrase the task slightly
- Change the order of context files read
- Summarize current state in your own words before retrying
- Small format changes in prompts break attention ruts
