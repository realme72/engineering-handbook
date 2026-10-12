# Time Complexity

## Why Does Time Complexity Matter?

When working with small datasets, almost every solution appears fast.

As the amount of data grows, the choice of algorithm and data structure has a significant impact on performance.

For example,

Searching for a user in a list of one million users is much slower than looking up the same user in a dictionary.

The difference isn't Python itself.

It's the underlying time complexity.

---

## What is Time Complexity?

Time complexity describes how the running time of an algorithm grows as the input size increases.

It focuses on the growth rate rather than the exact execution time.

```
Input Size (n)

        │

        ▼

Running Time
```

Instead of saying,

> "This function takes 25 ms."

we say,

> "This algorithm is O(n)."

because the growth pattern is more important than the exact timing.

---

## Common Time Complexities

| Complexity | Meaning | Example |
|------------|---------|---------|
| O(1) | Constant | Dictionary lookup |
| O(log n) | Logarithmic | Binary Search |
| O(n) | Linear | Traversing a list |
| O(n log n) | Linearithmic | Sorting |
| O(n²) | Quadratic | Nested loops |
| O(2ⁿ) | Exponential | Recursive brute force |

---

## Performance Growth

```
O(1)

•

•

•

•

Nearly Flat
```

```
O(log n)

•

  •

     •

        •
```

```
O(n)

•

  •

     •

        •

           •
```

```
O(n²)

•

      •

            •

                    •

                            •
```

As input grows,

small differences in complexity become huge.

---

# Python Collections

Choosing the right data structure usually has a much bigger impact than micro-optimizing code.

```
                Python Collections

                       │

      ┌────────────────┼────────────────┐

      ▼                ▼                ▼

     List            Dict              Set

      │                │                │

 Indexed         Hash Table       Hash Table

      │                │                │

 O(1) Index      O(1) Lookup      O(1) Lookup

 O(n) Search
```

---

# Lists

Lists are dynamic arrays.

```
Index

0 1 2 3

↓

[A][B][C][D]
```

---

## Common Operations

| Operation | Complexity |
|-----------|------------|
| Index Access | O(1) |
| Append | O(1) Amortized |
| Pop Last | O(1) |
| Search | O(n) |
| Insert Front | O(n) |
| Delete Front | O(n) |

---

## Why is Indexing O(1)?

Lists store elements in contiguous memory.

```
Memory

[A][B][C][D]
```

Python calculates the address directly.

```
Base Address

+

Index × Size

↓

Element
```

No searching is required.

---

## Why is Search O(n)?

Suppose

```python
x in numbers
```

Python checks each element one by one.

```
1

↓

2

↓

3

↓

4

↓

5
```

Worst case,

every element must be visited.

---

## Why is insert(0, value) O(n)?

Suppose

```
[A][B][C][D]
```

Insert at the front.

```
[X][A][B][C][D]
```

Every element shifts one position.

```
A →

B →

C →

D →
```

Hence,

```
O(n)
```

---

# Dictionaries

A dictionary is implemented using a **hash table**.

```
Hash

↓

Bucket

↓

Value
```

---

## Common Operations

| Operation | Complexity |
|-----------|------------|
| Lookup | O(1) Average |
| Insert | O(1) Average |
| Delete | O(1) Average |
| Iterate | O(n) |

---

## Why is Dictionary Lookup O(1)?

Suppose

```python
users[1001]
```

Python

```
Key

↓

Hash Function

↓

Bucket

↓

Value
```

Instead of searching every element,

Python jumps directly to the appropriate bucket.

---

## Can O(1) Become O(n)?

Yes.

If many keys produce the same hash,

they collide.

```
Hash

↓

Bucket

↓

A

↓

B

↓

C

↓

D
```

Now Python may need to search multiple entries.

Although collisions exist,

Python's hashing strategy keeps average lookup close to O(1).

---

# Sets

Sets are also implemented using hash tables.

The difference is

```
Dictionary

Key → Value
```

```
Set

Value Only
```

---

## Membership Test

```python
x in my_set
```

Average

```
O(1)
```

Whereas

```python
x in my_list
```

is

```
O(n)
```

---

# Sorting

Python uses **Timsort**.

Complexity

```
O(n log n)
```

Timsort combines ideas from Merge Sort and Insertion Sort.

It performs exceptionally well on partially sorted data.

---

# Choosing the Right Data Structure

```
Need indexing?

        │

       Yes

        ▼

      List



Need fast lookup?

        │

       Yes

        ▼

     Dictionary



Need uniqueness?

        │

       Yes

        ▼

        Set
```

---

# Real-World Examples

## Searching Users

Instead of

```python
for user in users:

    if user.id == target:
        return user
```

Use

```python
users[target]
```

Improvement

```
O(n)

↓

O(1)
```

---

## Removing Duplicates

Instead of

```python
unique = []

for item in data:

    if item not in unique:

        unique.append(item)
```

Use

```python
unique = set(data)
```

Average complexity becomes much lower due to constant-time membership checks.

---

## Counting Frequencies

Instead of

```python
count = {}

for word in words:

    ...
```

Use

```python
from collections import Counter
```

or

```python
defaultdict(int)
```

Both are optimized for this use case.

---

# Time Complexity Cheat Sheet

| Operation | List | Dict | Set |
|-----------|------|------|-----|
| Index | O(1) | ❌ | ❌ |
| Search | O(n) | O(1) Avg | O(1) Avg |
| Insert | O(1) Append | O(1) Avg | O(1) Avg |
| Delete | O(n) | O(1) Avg | O(1) Avg |
| Iterate | O(n) | O(n) | O(n) |

---

# Common Interview Questions

### What is time complexity?

Time complexity describes how an algorithm's running time grows as the input size increases. It focuses on scalability rather than exact execution time.

---

### Why is dictionary lookup O(1)?

Python dictionaries use a hash table. The key is hashed to determine the bucket where the value is stored, allowing direct access without scanning all elements.

---

### Why is searching a list O(n)?

Lists don't maintain an index based on values. Python checks each element sequentially until it finds a match or reaches the end.

---

### Why is `list.append()` O(1)?

Appending usually adds the element to the end of the allocated memory. Occasionally the list needs to resize, making a single append slower, but the average (amortized) complexity remains O(1).

---

### Why is `list.insert(0, x)` O(n)?

All existing elements must be shifted one position to the right to make room at the beginning of the list.

---

### Can dictionary lookup become O(n)?

Yes. In the worst case, excessive hash collisions can degrade lookup performance, although Python's hash table implementation keeps average lookup close to O(1).

---

### Why does Python use Timsort?

Timsort is stable, has O(n log n) worst-case complexity, and performs exceptionally well on partially sorted data, which is common in real-world applications.

---

### How do you choose between a list, set, and dictionary?

- Use a **list** when order and indexing matter.
- Use a **set** for fast membership checks and uniqueness.
- Use a **dictionary** for fast key-value lookups.

---

# Common Interview Mistakes

❌ Using a list for frequent lookups.

✔ Use a dictionary or set when fast membership or key-based access is required.

---

❌ Optimizing syntax instead of algorithms.

✔ Choosing the right algorithm or data structure usually has a much larger impact.

---

❌ Assuming O(1) means constant time in every situation.

✔ O(1) for hash tables is an average-case complexity. Worst-case performance can degrade due to collisions.

---

# Interview Tip

If asked,

> **"What's the biggest performance optimization you've made in Python?"**

A strong answer is:

> "The biggest improvements usually come from choosing the right data structure or algorithm. For example, replacing repeated list searches with dictionary lookups can reduce time complexity from O(n) to O(1), which has a much greater impact than micro-optimizing individual lines of code."

---

# Key Takeaways

- Time complexity measures how an algorithm scales with input size.
- Choosing the right data structure is often the biggest performance optimization.
- Lists provide fast indexing but slow searching.
- Dictionaries and sets use hash tables for fast average-case lookups.
- `list.append()` is amortized O(1), while inserting at the beginning is O(n).
- Python's sorting algorithm is Timsort with O(n log n) complexity.
- Always optimize algorithms and data structures before considering micro-optimizations.