# Mutable vs Immutable Objects

Python objects fall into two broad categories:

- **Mutable** – their internal state can change after creation.
- **Immutable** – it can't.

Mutability explains a lot of what looks confusing at first — how assignment behaves, how function arguments behave, why sharing an object between variables can bite you, and a good chunk of common interview questions.

---

## Mutable Objects

A mutable object can change without creating a new one.

```python
numbers = [1, 2, 3]

numbers.append(4)

print(numbers)
```

```python
[1, 2, 3, 4]
```

```
numbers
   │
   ▼
┌─────────────────┐
│ [1, 2, 3]       │
└─────────────────┘

append(4)

numbers
   │
   ▼
┌─────────────────┐
│ [1, 2, 3, 4]    │
└─────────────────┘
```

Same object throughout — only its contents changed.

---

## Immutable Objects

An immutable object can't be modified after creation. When it looks like one changed, Python actually built a new object and rebound the variable to it.

```python
name = "hello"

name += " world"

print(name)
```

```python
hello world
```

Before:

```
name
 │
 ▼
"hello"
```

After `name += " world"`, Python creates a brand new string:

```
Old Object

"hello"

New Object

name
 │
 ▼
"hello world"
```

The original `"hello"` was never touched.

---

## Mutable vs Immutable Using References

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

```python
a.append(3)
```

This modifies the existing list object:

```
a ─────┐
       ▼
 [1, 2, 3]
       ▲
b ─────┘
```

Since both variables point at the same object, both see the change:

```python
print(a)
print(b)
```

```
[1, 2, 3]
[1, 2, 3]
```

Now compare with something immutable:

```python
a = "hello"
b = a

a += " world"
```

Before:

```
a ─────┐
       ▼
   "hello"
       ▲
b ─────┘
```

After:

```
       "hello"
          ▲
b ─────────┘

a ───────► "hello world"
```

Instead of modifying `"hello"`, Python creates a new string and rebinds `a` — `b` still points at the original.

---

## Common Mutable Objects

- List
- Dictionary
- Set
- Bytearray
- Most user-defined class instances

```python
data = {
    "name": "Gaurav"
}

data["age"] = 25
```

The dict is modified in place.

---

## Common Immutable Objects

- Integer
- Float
- Boolean
- String
- Tuple
- Bytes
- Frozenset

```python
x = 10

x += 5
```

Python creates a brand new integer object with value `15` — it doesn't mutate `10`.

---

## Why are Strings Immutable?

Immutability buys a few real advantages:

- Safe sharing between variables
- String interning
- Faster hashing
- Better memory efficiency
- Thread safety

Since a string can never change, any number of variables can safely reference the same one without stepping on each other.

---

## Why are Tuples Immutable?

A tuple stores **references** to objects, and once created, those references can't be reassigned.

```python
t = (1, 2, 3)
```

Reading is fine:

```python
print(t[0])
```

Reassigning a slot isn't:

```python
t[0] = 10
```

```
TypeError: 'tuple' object does not support item assignment
```

The tuple simply won't let you swap out which objects it points to.

---

## Tuples Can Contain Mutable Objects

A common interview question:

```python
t = ([1, 2], [3, 4])

t[0].append(5)

print(t)
```

```python
([1, 2, 5], [3, 4])
```

The tuple itself was never touched — it still holds references to the same two list objects. What changed is the first list, in place, through one of those references.

Before:

```
Tuple
│
├──► [1,2]
└──► [3,4]
```

After:

```
Tuple
│
├──► [1,2,5]
└──► [3,4]
```

---

## Why Doesn't This Work?

```python
t = ([1, 2], [3, 4])

t[0] = [10, 20]
```

```
TypeError
```

This time you're trying to replace the reference the tuple holds at index 0, not mutate the object it points to:

```
Old

Tuple
│
├──► [1,2]
└──► [3,4]
```

```
Attempted

Tuple
│
├──► [10,20]   ❌
└──► [3,4]
```

Tuples don't allow that, regardless of what the object being swapped in looks like.

---

## Examples

### Example 1

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

### Example 2

```python
a = "hello"
b = a

a += " world"

print(a)
print(b)
```

Output:

```
hello world
hello
```

---

### Example 3

```python
t = ([1, 2], [3, 4])

t[0].append(5)

print(t)
```

Output:

```
([1, 2, 5], [3, 4])
```

---

## Follow-up Questions

### What is a mutable object?

One that can change after creation without a new object being created.

---

### What is an immutable object?

One that can't change after creation — any apparent modification creates a new object instead.

---

### Why are strings immutable?

It enables interning, faster hashing, better memory use, and thread safety.

---

### Why are tuples immutable?

Because the references stored inside a tuple can't be changed after it's created.

---

### Can an immutable object contain mutable objects?

Yes — a tuple can hold lists, dicts, or anything else mutable.

---

### Why does `tuple.append()` not exist?

Because a tuple can't change size or swap out the references it stores.

---

### Why does `t[0].append(5)` work?

The tuple itself is unchanged — you're mutating the list it points to, not the tuple.

---

### Why does `t[0] = []` fail?

Because that tries to replace one of the references stored inside the tuple, which tuples don't allow.

---

## Common Interview Mistakes

❌ Saying immutable means "stored in read-only memory."

✔ It means the object's state can't change after creation — nothing about where it lives in memory.

---

❌ Thinking variables become immutable.

✔ Variables are never mutable or immutable — objects are.

---

❌ Thinking tuples can't contain mutable objects.

✔ They can. The tuple stays immutable because its own references never change, even if what they point to does.

---

❌ Saying `+=` modifies strings.

✔ It creates a new string object and rebinds the variable — the original string is untouched.

---

## Key Takeaways

- Objects are either mutable or immutable.
- Mutable objects can be modified in place.
- Immutable objects can't be modified after creation — only replaced.
- Variables reference objects; mutability is a property of the object, never the variable.
- Rebinding a variable is different from modifying an object.
- Tuples are immutable because the references they store can't change.
- Tuples can still reference mutable objects whose own internal state changes freely.
