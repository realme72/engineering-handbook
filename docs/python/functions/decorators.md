# Decorators

## What is a Decorator?

A decorator is simply a function that takes another function as input, adds some additional behavior, and returns a new function.

One of the biggest reasons decorators work is because **functions are first-class objects** and **closures remember variables from their enclosing scope**.

A decorator doesn't modify the original function. Instead, it wraps the original function inside another function.

---

## How Does a Decorator Work?

Consider a simple function.

```python
def greet():
    print("Hello")
```

Now suppose we want to log every time this function is called.

Without decorators,

```python
print("Calling greet()")
greet()
```

This quickly becomes repetitive.

Instead, we can write a decorator.

```python
def logger(func):

    def wrapper():
        print(f"Calling {func.__name__}")
        return func()

    return wrapper
```

Now decorate the function.

```python
@logger
def greet():
    print("Hello")
```

Calling

```python
greet()
```

is actually equivalent to

```python
greet = logger(greet)

greet()
```

Output

```text
Calling greet
Hello
```

---

## How Python Executes a Decorator

When Python sees

```python
@logger
def greet():
    print("Hello")
```

Python internally converts it into

```python
def greet():
    print("Hello")

greet = logger(greet)
```

The name `greet` no longer points to the original function.

Instead,

```
greet
   │
   ▼
Wrapper Function
      │
      ▼
 Original Function
```

---

## Why Does This Work?

The decorator returns the `wrapper` function.

The `wrapper` function is a **closure**.

It remembers the original function through its closure.

```
             logger(func)

                  │
                  ▼

        Wrapper Function Object

      +---------------------------+
      | Bytecode                  |
      | Parameters                |
      | Closure                   |
      +-------------+-------------+
                    │
                    ▼
              func ─────────► greet()
```

Even after `logger()` finishes executing, the wrapper still remembers which function to execute.

That's why decorators are built on top of closures.

---

## Decorators With Arguments

Most decorators need to accept arbitrary arguments.

```python
def logger(func):

    def wrapper(*args, **kwargs):

        print(f"Calling {func.__name__}")

        return func(*args, **kwargs)

    return wrapper
```

This allows the decorator to wrap any function regardless of its parameters.

Example

```python
@logger
def add(a, b):
    return a + b

print(add(10, 20))
```

Output

```text
Calling add
30
```

---

## Preserving Function Metadata

One common issue is that decorators replace the original function.

```python
print(add.__name__)
```

Output

```text
wrapper
```

Instead of

```text
add
```

To preserve metadata, Python provides `functools.wraps`.

```python
from functools import wraps

def logger(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        print(f"Calling {func.__name__}")

        return func(*args, **kwargs)

    return wrapper
```

Now

```python
print(add.__name__)
```

Output

```text
add
```

---

## Parameterized Decorators

Sometimes decorators themselves need arguments.

```python
def repeat(times):

    def decorator(func):

        def wrapper(*args, **kwargs):

            for _ in range(times):
                func(*args, **kwargs)

        return wrapper

    return decorator
```

Usage

```python
@repeat(3)
def greet():
    print("Hello")
```

Output

```text
Hello
Hello
Hello
```

---

## Real-World Examples

### Flask

```python
@app.route("/users")
def get_users():
    ...
```

Registers an endpoint.

---

### FastAPI

```python
@app.get("/users")
def get_users():
    ...
```

Registers an HTTP GET endpoint.

---

### Authentication

```python
@login_required
def dashboard():
    ...
```

Checks authentication before executing the function.

---

### Timing

```python
@timeit
def process():
    ...
```

Measures execution time.

---

### Logging

```python
@logger
def create_order():
    ...
```

Logs every function call.

---

## Follow-up Questions

### What is a decorator?

A decorator is a function that takes another function, extends its behavior, and returns a new function.

---

### Why do decorators work?

Because functions are first-class objects and closures preserve references to the original function.

---

### What does the `@` syntax do?

It is syntactic sugar for

```python
func = decorator(func)
```

---

### Why do decorators usually use `*args` and `**kwargs`?

To support functions with any number of positional and keyword arguments.

---

### Why do we use `functools.wraps`?

To preserve the original function's metadata such as `__name__`, `__doc__`, and annotations.

---

### Can a decorator take parameters?

Yes.

Parameterized decorators return another decorator function.

---

## Common Interview Mistakes

❌ Thinking decorators modify the original function.

✔ They return a new wrapper function.

---

❌ Forgetting `*args` and `**kwargs`.

✔ Without them, the decorator only works for specific function signatures.

---

❌ Forgetting `functools.wraps`.

✔ Without it, function metadata is lost.

---

## Interview Tip

When asked about decorators, don't stop at saying:

> "A decorator adds extra functionality."

A stronger answer is:

> "A decorator is a higher-order function that takes a function object, creates a wrapper function using a closure, and returns that wrapper. The `@` syntax is simply syntactic sugar for reassigning the original function to the wrapper returned by the decorator."

That answer naturally connects first-class functions, closures, and decorators.

---

## Key Takeaways

- Functions are first-class objects.
- Decorators take a function and return another function.
- Decorators rely on closures to remember the original function.
- `@decorator` is syntactic sugar for `func = decorator(func)`.
- Use `*args` and `**kwargs` for generic decorators.
- Use `functools.wraps` to preserve function metadata.
- Decorators are heavily used in Flask, FastAPI, Django, logging, authentication, caching, and profiling.