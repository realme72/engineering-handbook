# Iterator Pattern

## Intent

I use the Iterator Pattern whenever clients need to traverse a collection without knowing how that collection stores its data internally.

If I notice business logic depending on whether data is stored as a list, tree, database cursor, or paginated API response, it's usually a sign that traversal should be separated from storage. The client should simply ask for the next element.

The primary goal is to separate **storage** from **traversal**.

---

## Why Was This Pattern Introduced?

Imagine order items were originally stored in a Python list. Later they're moved to a database cursor or Elasticsearch scroll. If every consumer knows the underlying data structure, changing storage breaks business logic. Instead, expose an iterator so clients simply call `next()` until the data ends.

---

## Software Engineering Examples

### Database Cursor

Application → Cursor → next() → Row

### Elasticsearch Scroll API

Application → Iterator → next() → Document

Both hide how data is actually stored.

---

## Python Implementation

```python
class OrderCollection:
    def __init__(self):
        self.items = ["Laptop", "Mouse", "Keyboard"]

    def __iter__(self):
        return OrderIterator(self.items)


class OrderIterator:
    def __init__(self, items):
        self.items = items
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index >= len(self.items):
            raise StopIteration
        item = self.items[self.index]
        self.index += 1
        return item


orders = OrderCollection()

for item in orders:
    print(item)
```

Python internally uses `iter()` and `next()` to power every `for` loop.

---

## Internal Workflow

Client
↓
Collection
↓
Iterator
↓
next()
↓
Element

---

## Advantages

- Hides collection implementation.
- Separates traversal from storage.
- Supports lazy loading.
- Works well with large datasets.

---

## Disadvantages

- Rarely implemented manually in Python.
- Extra abstraction for simple collections.

---

## Interview Answer

> I use the Iterator Pattern whenever I want clients to traverse a collection without depending on how the collection stores its data. The client shouldn't care whether the data comes from a list, a database cursor, or a paginated API. It simply requests the next element. This separation keeps traversal logic stable even if the underlying storage changes. Python's iterator protocol (`iter()` and `next()`) is a built-in implementation of this pattern.
