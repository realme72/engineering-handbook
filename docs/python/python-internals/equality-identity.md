# Equality vs Identity (`==` vs `is`)

`==` and `is` look similar but answer completely different questions:

- `==` asks: **do these two objects have the same value?**
- `is` asks: **do these two variables point at the exact same object?**

The distinction matters because Python variables hold **references to objects**, not the objects themselves.

---

## Equality (`==`)

`==` compares **values**. Internally, Python calls the object's `__eq__()` method to decide whether the two count as equal.

```python
a = [1, 2]
b = [1, 2]

print(a == b)
```

```python
True
```

`a` and `b` are two different list objects, but their contents match:

```
a ─────► [1, 2]

b ─────► [1, 2]
```

Different objects, same value — so `a == b` is `True`.

---

## Identity (`is`)

`is` compares **object identity** — whether two variables reference the same object.

```python
a = []
b = a

print(a is b)
```

```python
True
```

```
a ─────┐
       ▼
      []
       ▲
b ─────┘
```

Both variables point at the exact same list object.

---

## Comparing `==` and `is`

```python
a = [1, 2]
b = [1, 2]

print(a == b)
print(a is b)
```

```python
True
False
```

```
a ─────► [1,2]

b ─────► [1,2]
```

Same values, but two separate objects in memory — so `==` is `True` and `is` is `False`.

---

## Assignment Creates Shared References

```python
a = [1, 2]
b = a

print(a == b)
print(a is b)
```

```python
True
True
```

```
a ─────┐
       ▼
    [1,2]
       ▲
b ─────┘
```

Both variables point at the same object here, so both the value and the identity check come back true.

---

## Small Integer Caching (CPython)

One of the more common interview gotchas:

```python
a = 100
b = 100

print(a is b)
```

```python
True
```

CPython caches small integers, typically **-5 to 256**. Instead of allocating a fresh object every time one of these common values shows up, it reuses the same cached one:

```
          Small Integer Cache

                 100
                  ▲
          ┌───────┴───────┐
          │               │
          a               b
```

Both `a` and `b` reference that same cached object, so `a is b` is `True`.

---

## Larger Integers

```python
a = 1000
b = 1000

print(a is b)
```

You may see:

```python
False
```

Larger integers generally aren't cached — each assignment can create its own separate object.

> **Note:** This is a CPython implementation detail. Don't rely on it in application code.

---

## Why `==` Has Nothing to Do with Mutability

A common misconception is that mutable and immutable objects get compared differently. They don't.

```python
a = [1, 2]
b = [1, 2]

print(a == b)
```

```python
True
```

Lists are mutable, and `==` still returns `True` — because `==` compares values, full stop, regardless of whether the object happens to be mutable.

---

## When Should You Use `is`?

Use `is` specifically when you care about object identity, not value. The classic case is comparing against `None`:

```python
if value is None:
    print("No value")
```

rather than:

```python
if value == None:
```

`is None` is the idiomatic choice because `None` is a singleton — there's only ever one of it.

---

## Examples

### Example 1

```python
a = [1, 2]
b = [1, 2]

print(a == b)
print(a is b)
```

Output:

```python
True
False
```

---

### Example 2

```python
a = []
b = a

print(a == b)
print(a is b)
```

Output:

```python
True
True
```

---

### Example 3

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

### Example 4

```python
value = None

if value is None:
    print("No value")
```

Output:

```python
No value
```

---

## Follow-up Questions

### What is the difference between `==` and `is`?

`==` compares values. `is` compares whether two variables reference the same object.

---

### What does `==` call internally?

The object's `__eq__()` method.

---

### Does `is` compare memory addresses?

Not quite — it compares object identity. In CPython that usually maps to the memory address, but that's an implementation detail, not a guarantee.

---

### Why does `100 is 100` return `True`?

Because CPython caches small integers (roughly -5 to 256) and reuses the same object for them.

---

### Should you use `is` to compare numbers or strings?

No — use `==`. Reserve `is` for identity checks.

---

### Why do we write `is None` instead of `== None`?

Because `None` is a singleton, so an identity check is the correct, idiomatic way to test for it.

---

## Common Interview Mistakes

❌ Saying `is` compares memory addresses.

✔ It compares object identity — memory addresses are just a CPython implementation detail.

---

❌ Thinking `==` compares references.

✔ It compares values, via `__eq__()`.

---

❌ Using `is` to compare strings or integers.

✔ Use `==` for value comparisons.

---

❌ Thinking `==` behaves differently for mutable vs immutable objects.

✔ Mutability has no bearing on how `==` compares values.

---

## Key Takeaways

- `==` compares values; `is` compares object identity.
- `==` internally calls `__eq__()`.
- Reserve `is` for identity checks — comparing against singletons like `None` is the classic case.
- CPython caches small integers (roughly -5 to 256), so `100 is 100` is usually `True` — but this is an implementation detail, not something to depend on.
- Never use `is` for comparing numbers or strings — always use `==`.
