# Method Chaining

## What is Method Chaining?

Method chaining is a programming technique where multiple methods are called one after another on the same object.

This is possible because each method returns the object itself (`self`).

Instead of writing

```python
user.set_name("Alice")
user.set_age(25)
user.display()
```

we can write

```python
user.set_name("Alice").set_age(25).display()
```

The code becomes more readable and expressive.

---

## How Does Method Chaining Work?

Suppose we have

```python
class User:

    def set_name(self, name):

        self.name = name

        return self

    def greet(self):

        print(f"Hello {self.name}")

        return self
```

Usage

```python
User().set_name("Alice").greet()
```

Output

```
Hello Alice
```

Notice that every method returns

```python
self
```

This allows the next method to be called on the same object.

---

## Visualizing Method Chaining

```
User()

    │

    ▼

set_name("Alice")

    │

returns self

    ▼

greet()

    │

returns self

    ▼

display()
```

Every method hands back the same object.

---

## Memory Representation

```
                user

                  │

                  ▼

      +----------------------+

      | name = "Alice"       |

      +----------------------+

            ▲

            │

     return self

            │

            └───────────────┐
                            │
                            ▼
                    Next Method
```

No new object is created.

Each method returns a reference to the existing object.

---

## Why Does `return self` Matter?

Suppose

```python
class User:

    def set_name(self, name):

        self.name = name
```

Now,

```python
User().set_name("Alice").greet()
```

fails.

Why?

Because

```python
set_name()
```

returns

```python
None
```

Execution

```
User()

↓

set_name()

↓

None

↓

None.greet()

↓

AttributeError
```

Without `return self`, chaining breaks.

---

## Complete Example

```python
class User:

    def __init__(self):

        self.name = ""
        self.age = 0

    def set_name(self, name):

        self.name = name
        return self

    def set_age(self, age):

        self.age = age
        return self

    def display(self):

        print(self.name, self.age)
        return self
```

Usage

```python
User() \
    .set_name("Alice") \
    .set_age(25) \
    .display()
```

Output

```
Alice 25
```

---

## Builder Pattern

Method chaining is commonly used to implement the **Builder Pattern**.

```
Builder()

↓

set_engine()

↓

set_color()

↓

set_seats()

↓

build()
```

Every method returns the builder itself.

This creates a fluent interface.

---

## Real-World Examples

### Pandas

```python
(
    df
    .dropna()
    .sort_values("age")
    .head(10)
)
```

---

### SQLAlchemy

```python
(
    session.query(User)
    .filter(User.age > 18)
    .order_by(User.name)
    .all()
)
```

---

### Django ORM

```python
(
    User.objects
    .filter(active=True)
    .order_by("name")
)
```

---

### String Methods

```python
text.strip().lower().replace(" ", "_")
```

Each method returns another string.

---

## When Should You Use Method Chaining?

Method chaining works well when:

- Multiple operations naturally occur together.
- Each operation returns the same object.
- A fluent, readable API is desired.

Typical examples include:

- Builders
- Query Builders
- ORMs
- Data Processing Pipelines
- Configuration APIs

---

## When Should You Avoid It?

Avoid very long chains.

For example,

```python
obj.a().b().c().d().e().f().g().h()
```

This becomes difficult to debug.

Breaking the chain into multiple statements often improves readability.

---

## Common Interview Questions

### What is method chaining?

Method chaining is a technique where each method returns an object, allowing another method to be called immediately on the returned object.

---

### How is method chaining implemented?

It is typically implemented by returning `self` from each method.

---

### Why do we return `self`?

Returning `self` returns the same object, allowing subsequent method calls to operate on that object.

---

### Does method chaining create new objects?

Not necessarily.

If methods return `self`, the same object is reused.

Some immutable types, like strings, return **new objects** instead.

---

### Where is method chaining commonly used?

Method chaining is widely used in ORMs, query builders, builders, Pandas, SQLAlchemy, and many fluent APIs.

---

### Is method chaining related to the Builder Pattern?

Yes.

The Builder Pattern commonly uses method chaining to provide a fluent interface for constructing complex objects.

---

## Common Interview Mistakes

❌ Forgetting to return `self`.

✔ Without `return self`, chaining is not possible.

---

❌ Assuming chaining always modifies the same object.

✔ Mutable objects often return `self`, while immutable objects usually return a new object.

---

❌ Writing excessively long chains.

✔ Long chains reduce readability and make debugging harder.

---

## Interview Tip

If asked,

> **How does method chaining work internally?**

A strong answer is:

> "Method chaining works because each method returns an object. Most fluent APIs return `self`, allowing the next method to be invoked on the same object. Some immutable types instead return new objects, but the chaining mechanism remains the same."

---

## Key Takeaways

- Method chaining allows multiple methods to be called in a single expression.
- It is typically implemented by returning `self`.
- Chaining improves readability and creates fluent APIs.
- Mutable objects often return the same object, while immutable objects may return new ones.
- Method chaining is commonly used in builders, ORMs, and data-processing libraries.