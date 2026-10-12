# Object Interning

Object interning is a CPython optimization: instead of creating a fresh copy of an identical immutable object every time, Python reuses an existing one and just hands back a reference to it.

It mainly applies to:

- Small integers
- Strings

> **Note:** Interning is a CPython implementation detail. Never rely on it for correctness.

---

## Why Does Python Intern Objects?

Say a program creates the integer `100` thousands of times. Without interning, that's thousands of identical objects sitting in memory for no real reason:

```
100
100
100
100
100
```

Instead, Python creates one object and lets every variable that needs `100` reference it:

```
           Integer Object (100)
                   ▲
         ┌─────────┼─────────┐
         │         │         │
         a         b         c
```

Less memory, less object-creation overhead.

---

## Small Integer Caching

CPython caches integers in the range `-5` to `256`.

```python
a = 100
b = 100

print(a is b)
```

```python
True
```

```
        Small Integer Cache

              100
               ▲
       ┌───────┴───────┐
       │               │
       a               b
```

Both names point at the same cached object.

---

## Larger Integers

```python
a = 1000
b = 1000

print(a is b)
```

Outside the cached range, this can go either way depending on the implementation and how the code runs:

```python
False
```

Each variable might reference its own separate object — which is exactly why you should never use `is` to compare numbers. Use `a == b` instead.

---

## String Interning

CPython interns a lot of strings too, especially identifier-like ones: variable names, keywords, and some literals.

```python
a = "python"
b = "python"

print(a is b)
```

```python
True
```

Same underlying string object, reused rather than duplicated.

---

## Runtime Strings

Strings built at runtime don't always get interned the same way.

```python
a = "".join(["py", "thon"])
b = "python"

print(a == b)
print(a is b)
```

```python
True
False
```

Equal values, but possibly two different objects — since `a` was constructed at runtime rather than written as a literal.

---

## Manually Interning Strings

`sys.intern()` lets you force it:

```python
import sys

a = sys.intern("python")
b = sys.intern("python")

print(a is b)
```

```python
True
```

Useful if your code does a lot of repeated comparisons or lookups on the same set of strings.

---

## Why Interning Improves Performance

Without interning, two "identical" strings are really two separate objects:

```
Variable A ─────► "python"

Variable B ─────► "python"
```

With interning, there's just one:

```
           "python"
               ▲
       ┌───────┴───────┐
       │               │
       a               b
```

Less memory, faster object creation, faster identity checks, and better dictionary performance (since dict lookups lean on hashing and identity).

---

## Relationship with `is`

A classic interview trap:

```python
a = 100
b = 100

print(a is b)
```

```python
True
```

The tempting conclusion is "`is` must compare values here." It doesn't — `is` always compares identity. This returns `True` only because CPython happened to reuse the same cached object through interning, not because `is` suddenly started checking values.

---

## Examples

### Example 1

```python
a = 100
b = 100

print(a is b)
```

Output (CPython):

```python
True
```

---

### Example 2

```python
a = 1000
b = 1000

print(a == b)
print(a is b)
```

Typical output:

```python
True
False
```

---

### Example 3

```python
import sys

a = sys.intern("hello")
b = sys.intern("hello")

print(a is b)
```

Output:

```python
True
```

---

## Follow-up Questions

### What is object interning?

An optimization where Python reuses existing immutable objects instead of creating identical ones repeatedly.

---

### Which objects are commonly interned?

Small integers and many strings.

---

### What is the small integer cache?

CPython's cache of integers from `-5` to `256`.

---

### Does Python intern every string?

No — only certain ones automatically. Others can be interned manually with `sys.intern()`.

---

### Should you use `is` to compare numbers or strings?

No. Use `==`. `is` compares identity, not value.

---

### Is object interning part of the Python language?

No — it's a CPython implementation optimization, not a language guarantee.

---

## Common Interview Mistakes

❌ Thinking `is` compares values.

✔ It always compares object identity.

---

❌ Assuming every integer is cached.

✔ Only small integers, typically `-5` to `256`, are cached in CPython.

---

❌ Assuming every string is interned.

✔ Only certain strings are automatically interned.

---

❌ Relying on interning behavior in application code.

✔ Treat it as an optimization detail, not something to depend on.

---

## Key Takeaways

- Object interning is a CPython optimization.
- CPython caches small integers, typically `-5` to `256`.
- Many strings are interned too.
- Interning cuts memory use and speeds up object creation and identity checks.
- `is` compares object identity, never value.
- Never rely on interning for program correctness — use `==` for values, `is` for identity checks like `is None`.
