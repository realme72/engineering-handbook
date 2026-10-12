# Memory Optimization

## Why Does Memory Matter?

Performance isn't only about making code faster.

Memory is another critical resource.

An application that consumes excessive memory may:

- Crash with an Out of Memory (OOM) error.
- Trigger excessive garbage collection.
- Increase cloud infrastructure costs.
- Reduce overall system performance.

A good backend engineer optimizes both CPU and memory usage.

---

## Common Causes of High Memory Usage

```
            High Memory Usage

                   │

      ┌────────────┼────────────┐

      ▼            ▼            ▼

 Large Files   Large Lists   Duplicate Objects

      │            │            │

      ▼            ▼            ▼

 Streaming   Generators    Object Reuse
```

Most memory problems are caused by storing more data than necessary.

---

# Memory Optimization Principles

A simple rule is:

> **Don't keep data in memory if you don't need it.**

Whenever possible:

- Process data incrementally.
- Avoid unnecessary copies.
- Reuse existing objects.
- Choose appropriate data structures.

---

# Loading Large Files

Consider this example.

```python
with open("logs.txt") as file:

    lines = file.readlines()
```

`readlines()` loads the entire file into memory.

```
10 GB File

↓

Memory

↓

List of Lines
```

If the file is very large,

memory usage grows significantly.

---

## Streaming Large Files

Instead,

process one line at a time.

```python
with open("logs.txt") as file:

    for line in file:

        process(line)
```

Conceptually,

```
Read Line

↓

Process

↓

Discard

↓

Read Next Line
```

Only one line exists in memory at any given time.

---

# Lists vs Generators

Suppose we generate one hundred million numbers.

List

```python
numbers = [x * x for x in range(100000000)]
```

Memory

```
[1][4][9][16][25]...
```

Everything is stored.

---

Generator

```python
numbers = (x * x for x in range(100000000))
```

Conceptually,

```
Need Value?

↓

Generate

↓

Return

↓

Discard

↓

Generate Next
```

Only one value is kept in memory.

This makes generators ideal for processing large datasets.

---

## Visualization

Without Generator

```
Memory

[1][2][3][4][5][6][7][8][9]
```

Generator

```
Need Value?

↓

Generate 1

↓

Discard

↓

Generate 2

↓

Discard

↓

Generate 3
```

Memory usage remains almost constant.

---

# Avoid Unnecessary Copies

Suppose

```python
new_list = old_list.copy()
```

Now two complete lists exist.

```
Old List

↓

[Objects]



New List

↓

[Objects]
```

If the copy isn't required,

reuse the original object.

Creating unnecessary copies increases memory usage.

---

# Reusing Objects

Instead of repeatedly creating temporary objects,

reuse existing ones whenever possible.

Example

```python
buffer.clear()
```

instead of

```python
buffer = []
```

when appropriate.

Object reuse reduces memory allocations and garbage collection overhead.

---

# Choosing the Right Data Structure

Choosing the right data structure affects memory usage.

Suppose values never change.

Instead of

```python
colors = ["red", "green", "blue"]
```

consider

```python
colors = ("red", "green", "blue")
```

Tuples generally require less memory than lists because they are immutable.

---

## Remove Unused Objects

Large objects that are no longer needed should be released.

Instead of keeping

```python
huge_dataframe
```

alive throughout the application,

allow it to go out of scope once processing is complete.

This enables Python's garbage collector to reclaim memory.

---

# Streaming Data

Suppose you're processing one million database records.

Instead of

```
Load All Records

↓

Process
```

Prefer

```
Read Batch

↓

Process

↓

Discard

↓

Read Next Batch
```

Streaming or batching keeps memory usage predictable.

This approach is commonly used in ETL pipelines, log processing, and data migration jobs.

---

# Memory Optimization Checklist

```
Large File?

↓

Stream It



Large Collection?

↓

Use Generator



Repeated Copies?

↓

Reuse Objects



Immutable Data?

↓

Tuple



Large Dataset?

↓

Batch Processing
```

---

# Real-World Examples

## Processing Logs

Instead of

```python
logs = file.readlines()
```

Use

```python
for line in file:
    process(line)
```

---

## Reading Database Records

Instead of loading every row,

fetch records in batches.

```
Database

↓

100 Rows

↓

Process

↓

Next 100 Rows
```

---

## CSV Processing

Instead of loading the entire CSV,

iterate row by row.

This keeps memory usage almost constant regardless of file size.

---

## Image Processing

Instead of loading thousands of images,

load one image,

process it,

release it,

then continue with the next.

---

# Common Interview Questions

### What are the most common causes of high memory usage?

Large collections, loading entire files into memory, unnecessary object copies, and keeping objects alive longer than necessary are the most common causes.

---

### How do generators help reduce memory usage?

Generators produce values on demand instead of storing the entire sequence in memory, making them ideal for processing large datasets.

---

### Why is streaming better than loading everything into memory?

Streaming processes data incrementally, keeping memory usage almost constant regardless of the total data size.

---

### When should you use a tuple instead of a list?

Use a tuple when the data is immutable. Tuples generally consume less memory and clearly express that the data should not change.

---

### How can unnecessary object copies affect performance?

Copying large objects increases memory usage, allocation time, and garbage collection overhead. Reusing objects where appropriate is often more efficient.

---

### How would you optimize a Python application with high memory usage?

I would first identify what's consuming memory, then look for opportunities to stream data, replace large lists with generators, eliminate unnecessary copies, batch large datasets, and choose more memory-efficient data structures.

---

# Common Interview Mistakes

❌ Loading an entire file into memory.

✔ Stream large files whenever possible.

---

❌ Creating huge lists unnecessarily.

✔ Use generators for sequential processing.

---

❌ Keeping large objects alive after they're no longer needed.

✔ Release references so Python's garbage collector can reclaim memory.

---

❌ Copying large collections without a reason.

✔ Reuse existing objects whenever possible.

---

# Interview Tip

If asked,

> **"How do you optimize memory usage in Python?"**

A strong answer is:

> "I first identify where memory is being consumed. Then I look for opportunities to stream data instead of loading everything into memory, replace large lists with generators, eliminate unnecessary object copies, batch large datasets, and choose more memory-efficient data structures. Finally, I measure memory usage again to verify the improvement."

---

# Key Takeaways

- Memory optimization is about storing only the data you actually need.
- Stream large files instead of loading them entirely.
- Use generators for large sequential datasets.
- Avoid unnecessary object copies.
- Prefer tuples for immutable data.
- Process large datasets in batches.
- Always measure memory usage before and after optimization.