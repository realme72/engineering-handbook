# Python Memory Management

Python manages memory automatically through the **Python Memory Manager**.

Every Python object lives inside a **private heap**, managed by Python itself — the memory manager handles all allocation and deallocation from that heap.

The primary mechanism is **reference counting**: every object tracks how many references point to it, and the moment that count hits zero, the object is destroyed immediately. Reference counting alone can't reclaim **circular references**, though, so Python backs it up with a **generational garbage collector** that periodically finds and cleans up unreachable cycles.

For small objects, CPython also uses **pymalloc**, a specialized allocator that carves memory out of **arenas**, **pools**, and **blocks** to cut down on fragmentation and speed things up.

In short:

```
Python Memory Manager
        │
        ▼
   Private Heap
        │
        ▼
Reference Counting
        │
        ▼
Garbage Collector
        │
        ▼
pymalloc
```

---

# How Python Manages Memory

```
                   Python Program
                          │
                          ▼
               Python Memory Manager
                          │
            ┌─────────────┴─────────────┐
            │                           │
            ▼                           ▼
      Allocate Memory           Free Memory
            │                           │
            ▼                           ▼
      Private Heap             Reference Count
                                        │
                         Ref Count == 0 ?
                              │
                    ┌─────────┴─────────┐
                    │                   │
                   Yes                 No
                    │                   │
                    ▼                   ▼
          Deallocate Object     Garbage Collector
                                        │
                                        ▼
                          Remove Cyclic References
```

---

# Python Private Heap

## What is the Private Heap?

A region of memory reserved exclusively for Python objects — integers, strings, lists, dicts, sets, tuples, and every user-defined object all live here.

The operating system can't touch this memory directly. Only Python's own memory manager allocates or frees from it.

---

# Python Memory Manager

The **Python Memory Manager** handles:

- Allocating memory
- Deallocating memory
- Managing object lifetime
- Reusing freed memory
- Asking the OS for more memory when it's needed

It sits between your program and the operating system, and neither side talks to the other directly.

---

# Reference Counting

## What is Reference Counting?

Every Python object keeps a **reference count** — how many references currently point to it. The count goes up when a new reference is made, down when one goes away, and the object is destroyed the instant it hits zero.

---

## Example

```python
a = [1, 2, 3]
```

```
Reference Count = 1
```

```
a
 │
 ▼
[1,2,3]
```

```python
b = a
```

```
Reference Count = 2
```

```
a ───┐
     ▼
   [1,2,3]
     ▲
b ───┘
```

```python
del a
```

Reference count drops to `1` — the object is still alive because `b` still points to it.

```python
del b
```

Reference count drops to `0`, and Python deallocates the object right away.

---

# Why Reference Counting Isn't Enough

It falls apart on **cyclic references**:

```python
class Node:
    pass

a = Node()
b = Node()

a.next = b
b.next = a
```

Even after:

```python
del a
del b
```

the two objects still point at each other:

```
Node A ─────► Node B
   ▲            │
   └────────────┘
```

Their reference count never reaches zero — a **memory leak**, if reference counting were the only mechanism in play.

---

# Garbage Collection

This is exactly what the **generational garbage collector (GC)** handles — it periodically scans for unreachable cycles like this one and frees them.

---

# Generational Garbage Collection

Python groups objects into **three generations**:

```
Generation 0
       │
       ▼
Generation 1
       │
       ▼
Generation 2
```

Most objects die young. Anything that survives a few collection passes gets promoted to an older generation, which the GC scans less often — cutting down how much work each collection cycle actually has to do.

---

# pymalloc

CPython uses a specialized allocator called **pymalloc** for small objects, instead of asking the OS for memory on every single allocation. It manages its own pool of memory, which makes allocation considerably faster.

---

# Arenas, Pools and Blocks

```
Arena (256 KB)
│
├── Pool (4 KB)
│     ├── Block
│     ├── Block
│     ├── Block
│
├── Pool (4 KB)
│     ├── Block
│     ├── Block
│
└── Pool (4 KB)
```

- **Arena** – a large chunk requested from the OS.
- **Pool** – divides an arena into smaller regions.
- **Block** – the actual memory handed to a Python object.

This layered structure is what keeps fragmentation down and allocation fast.

---

# Examples

## Reference Counting

```python
import sys

a = []

print(sys.getrefcount(a))
```

---

## Cyclic Reference

```python
import gc

class Node:
    pass

a = Node()
b = Node()

a.next = b
b.next = a

del a
del b

gc.collect()
```

---

# Follow-up Questions

### What is Python's private heap?

The memory region where every Python object gets allocated.

---

### What is the Python Memory Manager?

The component responsible for allocating, managing, and freeing memory for Python objects.

---

### What is Reference Counting?

A count of how many references point to an object — when it hits zero, the object is deallocated.

---

### Why is Garbage Collection needed?

Reference counting can't reclaim cyclic references on its own. The garbage collector finds and removes those unreachable cycles.

---

### What are cyclic references?

Objects that reference each other, which keeps their reference count from ever reaching zero.

---

### What are the three GC generations?

Generation 0, 1, and 2 — objects that survive a collection get promoted to the next one up.

---

### What is pymalloc?

CPython's own optimized allocator for small objects.

---

### What are arenas, pools, and blocks?

Arenas split into pools, and pools split into blocks that hold individual Python objects.

---

# Common Interview Mistakes

❌ Saying Python only uses Garbage Collection.

✔ Reference counting does most of the work — GC only steps in for cyclic references.

---

❌ Thinking `del` deletes an object.

✔ `del` only removes a reference. The object itself is destroyed once its reference count hits zero.

---

❌ Assuming every allocation goes straight to the operating system.

✔ CPython routes small-object allocation through **pymalloc** instead.

---

# Key Takeaways

- Python objects live in the **Private Heap**.
- The **Python Memory Manager** controls allocation and deallocation.
- **Reference Counting** is the primary mechanism for reclaiming memory.
- **Garbage Collection** cleans up cyclic references reference counting can't touch.
- CPython uses **pymalloc** for fast small-object allocation.
- Memory is organized into **arenas**, **pools**, and **blocks**.
