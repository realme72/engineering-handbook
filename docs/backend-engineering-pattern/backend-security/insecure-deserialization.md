# Insecure Deserialization

# Why Does Insecure Deserialization Exist as a Vulnerability?

Deserialization turns a serialized representation — a byte stream, a string — back into a live object in memory. Some formats go further than plain data reconstruction: they're built to reconstruct arbitrary, complex objects, constructors and method calls included. Feed one of those formats untrusted data, and you've handed an attacker a way to make deserialization itself run code you never intended — often straight to remote code execution, not just a corrupted object.

```
Serialized data  →  DESERIALIZE  →  a live, usable object

↓

If the FORMAT itself supports reconstructing arbitrary objects
(calling arbitrary constructors, methods) as part of this process,
and the DATA comes from an untrusted source...

↓

An attacker who controls the serialized bytes can make
deserialization itself execute code they chose — before any
application-level validation ever even runs
```

---

# Python's `pickle` — The Canonical Example

```python
import pickle

# DANGEROUS if `data` comes from an untrusted source
obj = pickle.loads(data)
```

Pickle is designed to reconstruct arbitrary Python objects — a legitimate feature, useful for caching complex objects or passing them between processes. The same feature means a pickle payload can instruct deserialization to call arbitrary functions or constructors.

```python
import pickle, os

class Malicious:
    def __reduce__(self):
        return (os.system, ("rm -rf /important-data",))

payload = pickle.dumps(Malicious())

# elsewhere, on a DIFFERENT machine, deserializing this payload:
pickle.loads(payload)  # executes os.system("rm -rf /important-data") IMMEDIATELY
```

`__reduce__` is a documented, legitimate pickle mechanism for controlling how an object gets rebuilt. It's also exactly what lets an attacker who controls the bytes specify any function call they want — executed the instant `pickle.loads()` runs, before the application ever sees the resulting object.

---

# Why This Isn't an Ordinary Parsing Bug

Pickle isn't buggy here — it's doing what it was built to do. The problem is architectural: a format meant for trusted, internal data is being used on data that isn't trusted at all.

```
"We validated the deserialized OBJECT afterward, so we're safe"

↓

The dangerous code execution happens DURING deserialization
itself — pickle.loads() has ALREADY executed the attacker's
chosen code by the time any post-deserialization validation
logic would even run

↓

There is no "safe way" to validate AFTER the fact, because the
damage is already done by the time you'd get a chance to check
```

---

# The Real Fix: Never Deserialize Untrusted Data With a Trusted-Data Format

```
NEVER use for untrusted input:  pickle (Python), native Java
                                serialization, PHP's unserialize(),
                                YAML's default/unsafe loader in
                                some libraries — all formats
                                explicitly designed to reconstruct
                                arbitrary objects

USE for untrusted input:        JSON (a strictly data-only format —
                                 it can only represent strings,
                                 numbers, booleans, lists, and
                                 objects — never arbitrary code
                                 execution instructions), or a
                                 library's explicitly SAFE loader
                                 (e.g. yaml.safe_load() instead of
                                 yaml.load(), which restricts
                                 deserialization to plain data
                                 types only)
```

```python
# SAFE — JSON structurally cannot encode arbitrary object construction
import json
obj = json.loads(data)

# SAFE — YAML's safe loader restricts to plain data types
import yaml
obj = yaml.safe_load(data)  # NOT yaml.load(), which is unsafe by default in older versions
```

If you genuinely need to deserialize a richer, custom format from an untrusted source: sign the data cryptographically and verify the signature before deserializing, or use a strict, schema-validated parser that's structurally incapable of executing code. Not a general-purpose object-reconstruction format used carelessly.

---

# Real-World Examples

### Java Deserialization Vulnerabilities

Java's native serialization has the same architectural weakness as pickle, and a long history of serious CVEs across major frameworks trace directly back to deserializing untrusted data with it.

---

### Python's Own Official Documentation Warning About Pickle

Python's `pickle` docs say outright that it's "not secure" against erroneous or maliciously constructed data, and tell you never to unpickle anything from an untrusted or unauthenticated source. Not a subtle hint — the maintainers say it plainly.

---

### PHP Object Injection

`unserialize()` has a long history of similar issues — deserializing untrusted data can trigger "magic methods" on the reconstructed object, leading to unintended code execution much like pickle's `__reduce__`.

---

# Common Interview Questions

## What is insecure deserialization, and why can it lead to remote code execution?

Some formats — pickle, Java's native serialization — are built to reconstruct arbitrary objects, constructors and method calls included. Feed one untrusted data, and an attacker can craft a payload that specifies exactly which function gets called during deserialization, running arbitrary code before the application ever validates anything.

---

## Why is Python's pickle specifically dangerous to use on untrusted data?

Because `__reduce__` is a legitimate, documented feature that lets a serialized object control how it's rebuilt — including calling arbitrary functions. An attacker who controls the pickled bytes can specify any call they want, and it runs the moment `pickle.loads()` executes, before any validation gets a chance to look at it.

---

## How do you safely deserialize data that comes from an untrusted source?

Use a strictly data-only format like JSON, which can't encode object construction at all — or a library's explicitly safe loader (`yaml.safe_load()`, not `yaml.load()`). If you need a richer custom format, sign the data and verify the signature before deserializing, or use a schema-validated parser that can't trigger code execution by design.

---

## Why doesn't validating the object after deserialization protect against this?

Because the code runs during deserialization, not after. By the time a post-deserialization check would fire, the attacker's payload has already executed. There's no "check first" available after the fact — the vulnerable step already happened.

---

## Is caching pickled objects in Redis a security risk?

It can be, if the cache's contents could ever be influenced by untrusted input, or if the cache is reachable from a less-trusted context than whoever wrote to it assumed. The risk lives in the format and the data's origin, not in where the bytes happen to sit in the meantime.

---

# Common Mistakes

❌ Using pickle (or an equivalent arbitrary-object-reconstruction format) to deserialize any data that ultimately originates from an untrusted source.

Even indirect paths count — data cached and later read back, or accepted directly over an API — if the data's origin traces back to something an attacker could influence, the same risk applies.

---

❌ Assuming post-deserialization validation is a sufficient safeguard.

The dangerous code execution already happens during the deserialization call itself — validation logic that runs afterward is simply too late to prevent it.

---

❌ Using an unsafe default loader (like older versions' `yaml.load()`) without realizing a safe alternative exists.

Many libraries provide an explicitly restricted, safe loading function specifically for untrusted input — defaulting to the general-purpose loader without checking for a safer alternative is a common, easy-to-miss mistake.

---

# Key Takeaways

- Insecure deserialization happens when a format built to reconstruct arbitrary objects (pickle, Java's native serialization) is fed data from an untrusted source, letting a crafted payload execute code during deserialization itself.
- It's an architectural risk, not an ordinary bug — the format is doing exactly what it was designed to do; the mistake is pointing it at data it was never meant to handle.
- Post-deserialization validation can't help — the code execution already happened before any check could run.
- The real fix: a strictly data-only format (JSON) or a library's explicitly safe loader for anything untrusted, and reserve arbitrary-object-reconstruction formats for trusted, internal data only.
- Python's own docs warn against unpickling untrusted data directly — a rare, blunt acknowledgment of this exact risk from the language's own maintainers.
