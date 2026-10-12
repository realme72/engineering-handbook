# Namespaces & Scope

A **namespace** is a mapping between **names (identifiers)** and **objects**. Every time you create a variable, function, or class, Python stores that name inside a namespace — and namespaces are exactly what let the same name exist in different places without colliding.

```python
x = 10

def foo():
    x = 20
```

Both variables are named `x`, but Python knows exactly which one to use because they live in different namespaces.

---

## What is Scope?

**Scope** determines where a namespace is accessible — where Python looks when it needs to resolve a name.

```python
x = 10

def foo():
    x = 20
    print(x)

foo()

print(x)
```

```python
20
10
```

The first `print()` reads the local `x` inside `foo()`. The second reads the global `x` outside it.

---

## Types of Namespaces

Python has four namespaces.

### Local Namespace

Created every time a function runs, and destroyed when it returns.

```python
def greet():
    message = "Hello"

    print(message)
```

```
Local Namespace

message → "Hello"
```

---

### Enclosing Namespace

Created when one function is nested inside another.

```python
def outer():
    x = 20

    def inner():
        print(x)

    inner()
```

`x` belongs to `outer()`'s namespace. `inner()` doesn't have its own `x`, so Python looks one level out and finds it there.

```python
20
```

---

### Global Namespace

Holds anything defined outside every function, and lives for the entire life of the program.

```python
x = 100

def show():
    print(x)
```

```
Global Namespace

x → 100
show → function
```

---

### Built-in Namespace

Holds everything Python ships with — `print()`, `len()`, `sum()`, `list()`, `dict()`, `int()`, and the rest — all available without importing a thing.

---

## The LEGB Rule

Python resolves a name by searching, in order:

```
Local
   ↓
Enclosing
   ↓
Global
   ↓
Built-in
```

and stops the moment it finds a match.

```python
x = "Global"

def outer():
    x = "Enclosing"

    def inner():
        x = "Local"
        print(x)

    inner()

outer()
```

```text
Local
```

`inner()` has its own `x`, so the search stops right there — the enclosing, global, and built-in namespaces never even get checked.

Take away the local `x`:

```python
x = "Global"

def outer():
    x = "Enclosing"

    def inner():
        print(x)

    inner()

outer()
```

```text
Enclosing
```

Now `inner()` has no `x` of its own, so Python steps out one level and finds it in `outer()`'s namespace — still without ever reaching global.

And with no local *or* enclosing `x` at all:

```python
x = "Global"

def outer():
    def inner():
        print(x)

    inner()

outer()
```

```text
Global
```

This time the search runs all the way out to the global namespace before it finds a match. And if a name isn't defined anywhere in your code at all:

```python
print(len([1, 2, 3]))
```

Python falls all the way through to the **built-in** namespace, where `len()` lives.

---

## The `global` Keyword

Assigning to a variable inside a function normally creates a *local* variable, even if a global one shares the name:

```python
x = 10

def change():
    x = 20
```

This leaves the global `x` untouched. To actually modify it, say so explicitly:

```python
x = 10

def change():
    global x

    x = 20

change()

print(x)
```

```python
20
```

---

## The `nonlocal` Keyword

`nonlocal` does the same thing one level out — it lets a nested function modify a variable in its enclosing namespace instead of shadowing it.

```python
def outer():

    x = 10

    def inner():

        nonlocal x

        x = 20

    inner()

    print(x)

outer()
```

```python
20
```

Without `nonlocal`, `inner()` would just create its own local `x` and leave `outer()`'s copy untouched.

---

## `globals()` and `locals()`

`globals()` returns the global namespace as a dictionary:

```python
x = 10

print(globals()["x"])
```

```python
10
```

`locals()` does the same for whatever namespace you're currently in:

```python
def demo():

    x = 10

    print(locals())

demo()
```

```python
{'x': 10}
```

---

## Examples

### Example 1

```python
x = 100

def show():

    print(x)

show()
```

Output:

```python
100
```

---

### Example 2

```python
x = 100

def show():

    x = 200

    print(x)

show()

print(x)
```

Output:

```python
200
100
```

---

### Example 3

```python
def outer():

    x = 10

    def inner():

        print(x)

    inner()

outer()
```

Output:

```python
10
```

---

## Follow-up Questions

### What is a namespace?

A mapping between names and objects.

---

### What is scope?

Where a namespace is accessible — where Python looks when resolving a name.

---

### What are the four namespaces in Python?

Local, Enclosing, Global, and Built-in.

---

### What is the LEGB rule?

The order Python searches for a name: Local, then Enclosing, then Global, then Built-in — stopping at the first match.

---

### What does the `global` keyword do?

Lets a function modify a variable in the global namespace instead of creating a local shadow.

---

### What does `nonlocal` do?

Lets a nested function modify a variable in its enclosing namespace.

---

### What does `locals()` return?

A dictionary of the current local namespace.

---

### What does `globals()` return?

A dictionary of the global namespace.

---

## Common Interview Mistakes

❌ Thinking namespaces are memory locations.

✔ A namespace is a mapping between names and objects, not a place in memory.

---

❌ Confusing scope with namespace.

✔ A namespace stores names; scope determines where those names are visible.

---

❌ Forgetting the order of LEGB.

✔ Local → Enclosing → Global → Built-in.

---

❌ Thinking `global` and `nonlocal` are the same.

✔ `global` reaches the global namespace; `nonlocal` reaches the enclosing one.

---

## Key Takeaways

- A namespace is a mapping between names and objects.
- Scope determines where Python searches for a name.
- Python has four namespaces: Local, Enclosing, Global, and Built-in.
- Name resolution follows the LEGB rule, and stops at the first match.
- `global` modifies a variable in the global namespace; `nonlocal` modifies one in the enclosing namespace.
- `globals()` and `locals()` expose the current namespaces as dictionaries.
