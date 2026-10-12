# Command Injection

# Why Does Command Injection Exist as a Vulnerability?

Same root cause as SQL injection, different target. Instead of user input being read as SQL, it's read as **shell** syntax. Pass unsanitized input into a function that runs a shell command, and an attacker can slip in extra metacharacters or commands that the shell runs right alongside — or instead of — the one you intended.

```python
# DANGEROUS — user input concatenated into a shell command string
import os
os.system(f"ping {user_input}")
```

```
Attacker submits user_input:  8.8.8.8; rm -rf /important-data

↓

The shell receives:

ping 8.8.8.8; rm -rf /important-data

↓

The shell interprets the semicolon as a COMMAND SEPARATOR — it
runs `ping 8.8.8.8` AND THEN, as a completely separate command,
`rm -rf /important-data`
```

Nothing's broken here. Semicolons really do separate commands in shell syntax — the shell is doing its job. The bug is letting attacker-controlled input reach that parsing logic at all.

---

# The Real Fix: Avoid the Shell Entirely

Same idea as parameterized queries, applied to processes instead of databases: pass arguments as a **list** straight to the program, and skip the shell's interpretation of special characters altogether.

```python
# DANGEROUS — shell=True interprets the string as a shell command line
import subprocess
subprocess.run(f"ping {user_input}", shell=True)
```

```python
# SAFE — arguments passed as a list, executed WITHOUT a shell in between
subprocess.run(["ping", user_input])
```

```
With shell=True:  the string is handed to a SHELL, which parses
                  it for metacharacters (;, &&, |, `, $()) BEFORE
                  the actual program even runs — user input can
                  inject shell syntax at this parsing stage

Without shell=True (list form):  the arguments are passed DIRECTLY
                  to the program's exec call — there's no shell in
                  the middle at all to interpret metacharacters,
                  so "8.8.8.8; rm -rf /" is passed to ping as one
                  single, literal (if nonsensical) argument, never
                  parsed as multiple shell commands
```

Removing the layer that interprets input as syntax beats trying to sanitize every dangerous character after the fact — same lesson as SQL injection, one execution context over.

---

# Allowlisting as Defense in Depth

Even with the list-based approach, checking input against a strict, known-safe pattern first is worth doing. Not because the list form is insufficient — it's because defense in depth catches malformed input regardless of which specific mechanism is in play.

```python
import re

if not re.fullmatch(r"[\d.]+", user_input):  # only digits and dots — a plausible IP
    raise ValueError("Invalid input")

subprocess.run(["ping", user_input])
```

---

# Real-World Examples

### Countless CVEs in Tools Wrapping CLI Utilities

A recurring pattern across the industry: any tool that wraps a command-line utility — image processing via ImageMagick, network diagnostics via ping or traceroute, file conversion — is a candidate for command injection the moment it builds that command as a shell string instead of a list.

---

### Network Diagnostic Tools

A classic case. A web-based "ping this host" feature is one of the most common places this bug actually shows up, precisely because it feels like such an innocent thing to build by wrapping the shell command directly.

---

### Image Processing Pipelines

ImageMagick has a long history of command-injection-adjacent CVEs, largely because it's so often invoked by passing user-controlled filenames or options into a constructed shell command.

---

# Common Interview Questions

## How does command injection work? Walk through a concrete example.

User input reaches a function that runs a shell command, unsanitized. An attacker supplies shell metacharacters — a semicolon, say — that the shell reads as a command separator, letting their own command run alongside the intended one. `os.system(f"ping {user_input}")` with input `8.8.8.8; rm -rf /` runs both the ping and the destructive delete.

---

## Why does passing arguments as a list instead of a shell string fix this?

It skips the shell entirely. A list of arguments goes straight to the program's exec call, with nothing in between to parse semicolons or pipes. Whatever the user supplies becomes one literal argument, never multiple shell commands — the vulnerability is eliminated structurally, not patched around.

---

## Why is `shell=True` in Python's `subprocess` considered dangerous by default?

Because it hands the command string to an actual shell, which interprets metacharacters — `;`, `&&`, `|`, backticks, `$()` — before the real program even runs. Any user input reaching that string can inject its own shell syntax. The list-based form of `subprocess.run` never invokes a shell, so none of that applies.

---

## Is basic character escaping (blocking semicolons, for instance) a sufficient fix?

No. Shell metacharacters and injection tricks go well beyond the obvious ones — pipes, backticks, command substitution, even newlines in some contexts — and escaping is easy to get subtly wrong. Avoiding the shell via the list-based form is the real fix; allowlisting is a good complement, not a substitute.

---

# Common Mistakes

❌ Using `shell=True` (or an equivalent shell-invoking call) with any user-controlled input.

Hands attacker-controlled data directly to a shell capable of interpreting it as command syntax — the root cause of every command injection vulnerability.

---

❌ Building a shell command string via concatenation or f-strings before executing it.

Some functions and languages construct and pass a command string to a shell by default, even without an explicit `shell=True` flag — check whether a given execution API invokes a shell before assuming it's safe.

---

❌ Assuming basic character escaping (blocking a semicolon, for instance) is sufficient.

There are too many shell metacharacters and encoding tricks to escape your way out reliably. Avoiding the shell entirely is the real fix.

---

# Key Takeaways

- Command injection happens when user input reaches a shell's command-parsing logic, letting it be read as extra shell syntax instead of a single intended argument.
- The real fix is passing arguments as a list directly to the program, bypassing the shell — the same structural idea as parameterized queries, applied to process execution.
- `shell=True` (and its equivalents in other languages) should never touch user-controlled input, since it hands attacker data straight to a shell that can interpret it as commands.
- Allowlisting is a reasonable extra layer, but it doesn't replace avoiding the shell as the primary fix.
- Tools that wrap CLI utilities — network diagnostics, image processing — are the most common real-world source of this bug, precisely because they seem like such innocent features to build.
