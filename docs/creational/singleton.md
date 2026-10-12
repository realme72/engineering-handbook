# Singleton Pattern

## Intent

The Singleton Pattern ensures that a class has only one instance throughout the lifetime of an application while providing a single, globally accessible point to that instance.

It is useful when multiple instances of an object could lead to inconsistent state, unnecessary resource consumption, or conflicting behavior.

---

## Why Was This Pattern Introduced?

Take a logging system in a web application.

A naive implementation creates a new `Logger` object on every incoming request.

```python
def create_user():
    logger = Logger()

def update_user():
    logger = Logger()

def delete_user():
    logger = Logger()
```

It looks harmless at first. But once the app scales to thousands of requests, you're spinning up a new logger for every single one.

The real cost isn't memory. Logging is a shared, application-wide service — every component should be writing to the *same* logger, not keeping its own copy.

Multiple logger instances mean:

- Duplicate initialization of log handlers.
- Inconsistent logging configuration.
- Several objects competing to manage the same resource.
- Object creation and garbage collection overhead you don't need.

Singleton fixes this by guaranteeing exactly one `Logger` instance for the app's entire lifetime.

---

## Real-World Analogy

Think of a company's CEO.

Every employee deals with the same CEO — the company doesn't hire a new one every time someone needs sign-off.

Same idea here: every part of an application should talk to the same `Logger`, `Configuration Manager`, or `Cache Manager` instead of spinning up new instances.

---

## Software Engineering Example

A configuration manager is a classic real-world case for Singleton.

Without Singleton:

```python
config1 = ConfigManager()
config2 = ConfigManager()
config3 = ConfigManager()
```

Each object reads the same configuration file from disk, independently.

That means:

- Duplicate file I/O
- Duplicate memory usage
- Multiple copies of identical configuration data

Load it once. Share it across every module instead.

---

## Python Implementation

```python
class Singleton:

    _instance = None

    def __new__(cls):

        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance
```

---

## How It Works Internally

Creating an object with

```python
obj = Singleton()
```

triggers two steps internally.

### Step 1

```python
__new__()
```

Creates the object in memory.

### Step 2

```python
__init__()
```

Initializes the object.

Singleton intercepts the object creation phase by overriding `__new__()`.

During the first call:

```text
Singleton()

↓

__new__()

↓

_instance == None

↓

Create object

↓

Store inside _instance

↓

Return object
```

During subsequent calls:

```text
Singleton()

↓

__new__()

↓

_instance already exists

↓

Return existing object
```

No new object is created.

---

## Code Walkthrough

### Why override `__new__()` instead of `__init__()`?

`__new__()` creates the object; `__init__()` only initializes one that already exists.

Since Singleton needs to control **whether a new object gets created at all**, that decision has to live in `__new__()`.

---

### Why is `_instance` a class variable?

A class variable is shared across every instance of the class.

Make it an instance variable instead, and every object gets its own copy — defeating the whole point.

---

### Why use `super().__new__(cls)`?

`Singleton` doesn't know how to allocate memory for a new object on its own.

It delegates that to Python's base `object` class via `super().__new__(cls)`, then stores the result in `_instance`.

---

## Advantages

- Guarantees a single instance of a shared resource.
- Prevents duplicate initialization.
- Provides a globally accessible object.
- Centralizes application-wide state.

---

## Disadvantages

- Introduces global state, making testing more difficult.
- Creates tight coupling between components.
- Can become a bottleneck if overused.
- Requires additional synchronization in multithreaded applications.

---

## When Should You Use It?

Use Singleton when:

- Exactly one instance should exist.
- The object manages a shared resource.
- Every component should access the same object.

Examples include:

- Logger
- Configuration Manager
- Cache Manager
- Thread Pool Manager
- Database Connection Pool Manager

---

## When Should You Avoid It?

Avoid Singleton when:

- Multiple independent instances are expected.
- The object holds request-specific or user-specific state.
- Dependency Injection provides a cleaner solution.
- Shared global state makes testing difficult.

---

## Common Interview Questions

### Basic

- What problem does the Singleton Pattern solve?
- Why is `__new__()` overridden instead of `__init__()`?

### Intermediate

- Is this implementation thread-safe?
- Why is `_instance` a class variable?

### Advanced

- How can Singleton be implemented using a metaclass?
- How would you make this implementation thread-safe?
- Can Singleton be broken using multiprocessing or serialization?

---

# Related Patterns

| Pattern | Difference |
| ------- | ---------- |
| Factory Method | Factory Method decides **which object** to create. Singleton decides **how many objects** may exist. |
| Builder | Builder focuses on constructing complex objects. Singleton controls object lifetime. |
| Prototype | Prototype creates objects by cloning existing ones. Singleton restricts object creation to a single instance. |

---

## Key Takeaways

- Singleton guarantees that only one instance of a class exists.
- It controls object creation by overriding `__new__()`.
- The primary motivation is managing shared resources consistently, not merely saving memory.
- Use Singleton only when a single shared instance is a genuine requirement.