# Prototype Pattern

## Intent

The Prototype Pattern creates new objects by **cloning an existing object** instead of constructing one from scratch.

Instead of repeatedly creating and initializing similar objects, the application creates a copy of an existing object and modifies it if needed.

---

## Why Was This Pattern Introduced?

Suppose you're developing a game where creating a character involves loading animations, textures, weapons, and configuration files.

A naive implementation creates a new object every time.

```python
warrior1 = Warrior()

warrior2 = Warrior()

warrior3 = Warrior()
```

If object creation is expensive, every new object repeats the same initialization process.

Problems with this approach:

- Expensive object creation.
- Repeated initialization.
- Poor performance when many similar objects are needed.

Prototype solves this by fully initializing one object once, then cloning it whenever another similar one is needed.

---

## Real-World Analogy

Think of a finished resume. You don't write a new one from scratch for every job — you copy it and tweak a few details.

Prototype works the same way: copy an existing object instead of building a new one from nothing.

---

## Software Engineering Example

Say a company generates employee profiles.

Instead of repeatedly creating near-identical employee objects,

```python
emp1 = Employee("Alice", "Engineer")
emp2 = Employee("Bob", "Engineer")
emp3 = Employee("Charlie", "Engineer")
```

clone one prototype instead — no repeated initialization.

Common real-world examples include:

- Game characters
- Document templates
- UI templates
- Configuration objects
- Machine Learning models
- Expensive database objects

---

## Python Implementation

```python
import copy


class Employee:

    def __init__(self, name, role):
        self.name = name
        self.role = role


emp1 = Employee("Alice", "Engineer")

emp2 = copy.deepcopy(emp1)
emp2.name = "Bob"

print(emp1.name)   # Alice
print(emp2.name)   # Bob
```

---

## How It Works Internally

When we clone an object,

```
Existing Object

↓

copy.deepcopy()

↓

Create New Object

↓

Copy all attributes

↓

Return Independent Clone
```

The cloned object has its own memory.

Changing the clone does **not** affect the original object.

---

## Code Walkthrough

### Why use `copy.deepcopy()`?

`deepcopy()` creates a completely independent copy of an object.

Changes made to the cloned object do not affect the original object.

---

### What is shallow copy?

```python
copy.copy(obj)
```

Creates a new object, but nested mutable objects are still shared.

Example:

```python
import copy

a = [[1, 2]]

b = copy.copy(a)

b[0].append(3)

print(a)
```

Output

```text
[[1, 2, 3]]
```

Both objects share the same nested list.

---

### What is deep copy?

```python
copy.deepcopy(obj)
```

Creates a completely independent copy.

Example:

```python
import copy

a = [[1, 2]]

b = copy.deepcopy(a)

b[0].append(3)

print(a)
```

Output

```text
[[1, 2]]
```

The original object remains unchanged.

---

## Advantages

- Faster than expensive object creation.
- Avoids repeating initialization logic.
- Simplifies creating similar objects.
- Improves performance when object creation is costly.

---

## Disadvantages

- Deep copying large object graphs can be expensive.
- Circular references require careful handling.
- Not every object can be cloned safely.

---

## When Should You Use It?

Use Prototype when:

- Object creation is expensive.
- Many similar objects are required.
- Objects differ only slightly after creation.
- Initialization involves heavy computation or I/O.

Examples include:

- Game characters
- Document templates
- UI templates
- Configuration objects
- Machine learning models

---

## When Should You Avoid It?

Avoid Prototype when:

- Object creation is inexpensive.
- Objects contain resources that cannot be copied safely.
- Every object is fundamentally different.

---

## Common Interview Questions

### Basic

- What problem does the Prototype Pattern solve?
- Why use cloning instead of creating a new object?

### Intermediate

- What is the difference between shallow copy and deep copy?
- Why is `deepcopy()` generally preferred?

### Advanced

- How would you clone an object with circular references?
- How would you implement Prototype without Python's `copy` module?

---

## Related Patterns

| Pattern | Difference |
|----------|------------|
| Builder | Builder constructs complex objects step by step. Prototype clones an existing object. |
| Factory Method | Factory Method decides which object to create. Prototype copies an existing object. |
| Singleton | Singleton restricts the number of instances. Prototype creates multiple instances by cloning. |

---

## Key Takeaways

- Prototype creates new objects by cloning existing ones.
- It avoids expensive object initialization.
- `copy.deepcopy()` creates completely independent clones.
- Prototype is useful when many similar objects need to be created efficiently.