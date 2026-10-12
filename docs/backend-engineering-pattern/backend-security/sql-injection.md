# SQL Injection

# Why Does SQL Injection Exist as a Vulnerability?

A SQL query is built from two different things: fixed structure written by a developer, and data supplied by a user. Mix them carelessly — concatenate user input straight into a query string — and an attacker's input stops being data and starts being SQL **syntax**. That's the whole vulnerability in one sentence.

```python
# DANGEROUS — user input concatenated directly into the query string
query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
```

```
Attacker submits username:  ' OR '1'='1

↓

The query becomes:

SELECT * FROM users WHERE username = '' OR '1'='1' AND password = '...'

↓

'1'='1' is ALWAYS true — the WHERE clause matches every row in
the table, and the attacker is logged in as the FIRST user
returned, without ever knowing a real password at all
```

The database isn't malfunctioning — it's executing exactly the SQL it was handed. The bug is that user-controlled input got to decide what SQL that was.

---

# Data Exfiltration via UNION-Based Injection

Beyond bypassing a login, injection can pull data the query was never meant to return.

```sql
-- Original, intended query:
SELECT name, price FROM products WHERE id = '5'
```

```
Attacker submits id: 5' UNION SELECT username, password FROM users --

↓

Resulting query:

SELECT name, price FROM products WHERE id = '5' UNION SELECT
username, password FROM users --'

↓

The UNION appends an ENTIRELY DIFFERENT table's data (usernames
and passwords) onto the result set the application displays as
if it were normal product data
```

Injection isn't limited to whatever the original query was "supposed" to do. A well-crafted payload can read — or, against a mutating query, modify or delete — anything else in the database too.

---

# The Real Fix: Parameterized Queries

Escaping special characters is fragile; it's easy to miss an edge case. The real fix sends the query structure and the user-supplied data **separately** to the database, so input can never be read as syntax, no matter what it contains.

```python
# SAFE — parameterized query
cursor.execute(
    "SELECT * FROM users WHERE username = %s AND password = %s",
    (username, password),
)
```

```
The database receives:

1. The QUERY STRUCTURE (with placeholders) — sent and compiled FIRST
2. The DATA VALUES — sent SEPARATELY, bound into those placeholders

↓

Even if username literally contains ' OR '1'='1, the database
treats it as a LITERAL STRING VALUE to search for, never as SQL
syntax to be parsed and executed — the injection has NOWHERE to
"break out" into, because the query structure was already fixed
before the data was ever attached
```

That's the difference between parameterization and escaping: escaping neutralizes specific characters after the fact and can always miss one; parameterization never lets data and syntax touch in the first place.

---

# ORMs — A Natural Mitigation, With a Real Caveat

Most ORM query builders (SQLAlchemy, Django's ORM, ActiveRecord) parameterize automatically. That's one of the quiet, genuine benefits of using the ORM's own API instead of hand-writing SQL.

```python
# Safe — Django ORM builds a parameterized query automatically
User.objects.filter(username=username, password=password)
```

```python
# STILL VULNERABLE — raw SQL constructed via string formatting, even inside an ORM-based codebase
User.objects.raw(f"SELECT * FROM users WHERE username = '{username}'")
```

The protection only holds while you stay inside the ORM's query-building interface. Drop down to raw SQL — a common escape hatch for a query the ORM can't easily express — and string-concatenate user input into it, and the exact same hole reopens.

---

# Second-Order SQL Injection — A Subtler Variant

Easy to miss: data stored safely once, via a properly parameterized `INSERT`, can still cause injection later if some other part of the codebase reads it back and concatenates it into a different query.

```python
# Step 1: user's malicious "name" is safely stored via parameterized INSERT
cursor.execute("INSERT INTO users (name) VALUES (%s)", (malicious_name,))

# Step 2, elsewhere in the codebase, LATER: the stored name is
# read back and unsafely concatenated into a DIFFERENT query
cursor.execute(f"SELECT * FROM logs WHERE user = '{user.name}'")  # VULNERABLE
```

The first query was fine. The danger was just deferred — the payload sits in the database waiting for whichever piece of code eventually handles it carelessly.

---

# Real-World Examples

### Countless Major Breaches Attributed to SQL Injection

One of the most common root causes of real data breaches in the industry's history — common enough that "SQL injection" is close to a household term in security circles, because the bug is trivial to introduce by accident and brutal when exploited.

---

### Login Bypass as a Classic Penetration-Testing Check

The `' OR '1'='1` trick is one of the first things any security review or pen test throws at a login form. Simple, severe, and standard enough that it's practically baseline.

---

### ORM Raw Query Escape Hatches

A recurring real-world source of SQL injection even in modern, ORM-based codebases. A developer hits a query the ORM's abstraction can't express cleanly, reaches for a raw query, and re-introduces string concatenation without noticing.

---

# Common Interview Questions

## How does SQL injection actually work? Walk through a concrete example.

User input gets concatenated into a SQL query string instead of being treated as data. An attacker supplies input that's really SQL syntax — like `' OR '1'='1` — and it changes the query's logic when it runs. On a login form, that can make the WHERE clause always evaluate true, bypassing authentication without knowing a single real credential.

---

## Why do parameterized queries fully solve this, rather than just reducing the risk?

Because the query structure and the data are sent to the database separately. The structure is compiled before any user value is attached, so that value is always treated as a literal to search for or insert — never as syntax to parse. There's no way for injected input to "break out," which isn't true of escaping, which just tries to neutralize dangerous characters and can miss one.

---

## Can using an ORM still leave you vulnerable to SQL injection?

Yes. The ORM's standard query-building methods parameterize automatically, but most ORMs also expose a raw-SQL escape hatch for queries the standard API can't easily express. Concatenate user input into that raw SQL, and the same vulnerability comes right back, ORM or not.

---

## What is second-order SQL injection?

Data stored safely through a parameterized `INSERT`, then read back and unsafely concatenated into a different query somewhere else in the codebase. The storage step was fine — the danger was just deferred to whatever code mishandles the already-stored payload later.

---

# Common Mistakes

❌ Concatenating or string-formatting user input directly into a SQL query.

The root cause of every SQL injection vulnerability — use parameterized queries or the ORM's standard query builder instead.

---

❌ Assuming ORM usage automatically guarantees immunity to SQL injection.

Raw or manually-constructed queries inside an ORM-based codebase carry the exact same risk if user input is concatenated into them.

---

❌ Relying on escaping or sanitization alone instead of parameterization.

Escaping is fragile and easy to get subtly wrong. Parameterized queries remove the vulnerability structurally, by never letting user data and query syntax mix.

---

# Key Takeaways

- SQL injection happens when user input is concatenated into a query string, letting an attacker's input be read as SQL syntax instead of data.
- Parameterized queries are the real fix — sending structure and data separately means input can never be interpreted as syntax, no matter what it contains.
- ORMs parameterize automatically through their standard query builder, but their raw-SQL escape hatches reopen the same risk.
- Second-order SQL injection shows that safe storage once doesn't mean safety forever — the same data reused carelessly in a later query is just as exploitable.
- SQL injection is still one of the most common, most damaging vulnerabilities in web applications — easy to introduce by accident, and structurally easy to prevent once you understand it.
