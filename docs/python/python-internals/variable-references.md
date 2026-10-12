# Variables & References

In Python, **variables don't store values directly** — they store **references** (bindings) to objects in memory.

This single idea explains a surprising amount of Python's behavior: assignment, function arguments, mutable objects, copying, memory management. Once it clicks, a lot of "weird" Python behavior stops being weird.

---

## Variables are References

```python
a = 10
```

Most people read this as "`a` stores the integer `10`." That's not quite what happens. Python creates (or reuses) an integer object `10`, and `a` is bound to it:

```
a ─────────────► Object
                ┌──────────────┐
                │ Type : int   │
                │ Value: 10    │
                └──────────────┘
```

`a` isn't the object — it's just a name that points to one.

---

## Multiple Variables Can Reference the Same Object

```python
a = 10
b = a
```

```
a ─────┐
       ▼
      10
       ▲
b ─────┘
```

Both variables point at the same integer object — Python doesn't create a second one. You can confirm this with `id()`:

```python
a = 10
b = a

print(id(a))
print(id(b))
```

```
140731489305104
140731489305104
```

Same identity, both times.

---

## Reassignment Changes the Reference

```python
a = 10
b = a

a = 20
```

Python doesn't modify the object `10` — it rebinds `a` to a different object entirely.

Before:

```
a ─────┐
       ▼
      10
       ▲
b ─────┘
```

After:

```
       10
       ▲
b ─────┘

a ─────────────► 20
```

The object `10` was never touched. Only what `a` points to changed.

---

## Modifying an Object vs Rebinding a Variable

```python
a = [1, 2]
b = a
```

```
a ─────┐
       ▼
    [1, 2]
       ▲
b ─────┘
```

Now mutate the list:

```python
a.append(3)
```

```
a ─────┐
       ▼
   [1, 2, 3]
       ▲
b ─────┘
```

The list itself was modified in place, and since both variables reference that same object, both see the change:

```python
print(a)
print(b)
```

```
[1, 2, 3]
[1, 2, 3]
```

---

## Rebinding is Different

```python
a = [1, 2]
b = a

a = [5, 6]
```

```
Old List

       [1,2]
          ▲
b ─────────┘

New List

a ─────────► [5,6]
```

The original list is untouched — `a` now points at a completely different list.

```python
print(a)
```

```
[5, 6]
```

```python
print(b)
```

```
[1, 2]
```

---

## Variables Don't Own Objects

Objects exist independently of whatever variables happen to point at them.

```python
a = [1, 2]
b = a

del a
```

```
[1,2]
   ▲
b──┘
```

`del a` didn't delete the list — it just removed one reference to it. `b` still holds a reference, so the list is still alive. Only once the last reference disappears can Python reclaim the memory.

---

## Variables, References and Memory

```
Variable
   │
   ▼
Reference
   │
   ▼
Python Object
   │
   ├── Identity
   ├── Type
   └── Value
```

Keep this chain in mind whenever you're reasoning about what a piece of Python code actually does.

---

## Examples

### Example 1

```python
a = 10
b = a

print(id(a))
print(id(b))
```

Output:

```
Same object identity
```

---

### Example 2

```python
a = [1, 2]
b = a

a.append(3)

print(a)
print(b)
```

Output:

```
[1, 2, 3]
[1, 2, 3]
```

---

### Example 3

```python
a = [1, 2]
b = a

a = [5, 6]

print(a)
print(b)
```

Output:

```
[5, 6]
[1, 2]
```

---

## Follow-up Questions

### Are Python variables pointers?

Not really. They're names bound to objects — unlike C pointers, they can't do pointer arithmetic or touch memory directly.

---

### Do variables store objects?

No, they store references to objects.

---

### What happens when we execute `a = b`?

No new object gets created — both names end up pointing at the same one.

---

### What happens during reassignment?

The variable gets rebound to a different object. The original object is left alone.

---

### Does `del` delete an object?

No. It removes a reference. The object itself only goes away once no references to it remain.

---

### Why does modifying a list affect another variable pointing to it?

Because both variables reference the same underlying object, and the mutation happens on that object in place.

---

## Common Interview Mistakes

❌ Saying variables store values.

✔ Variables store references to objects.

---

❌ Saying `a` is an object.

✔ `a` is a name. The object is whatever it references.

---

❌ Thinking `a = b` copies an object.

✔ It copies the reference — not the object.

---

❌ Thinking `del` immediately destroys an object.

✔ `del` removes a reference. The object survives until nothing references it anymore.

---

## Key Takeaways

- Variables are names bound to objects, not the objects themselves.
- Multiple variables can reference the same object.
- Assignment copies the reference, not the object.
- Reassignment changes the reference, not the object.
- Modifying an object is different from rebinding a variable.
- `del` removes a reference — not necessarily the object.
