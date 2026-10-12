# Closures

## What is a Closure?

A closure is a **function object that remembers variables from its enclosing scope even after the enclosing function has finished executing.**

Consider the following example:

```python
def outer():

    x = 10

    def inner():
        print(x)

    return inner
```

When `outer()` returns, its local namespace is normally destroyed.

However, the returned function `inner()` still needs access to `x`.

Instead of destroying `x`, Python preserves it by storing a reference to it inside the returned function object's **closure**.

This allows `inner()` to access `x` even though `outer()` has already finished executing.

---

## How Does a Closure Work?

```python
def outer():

    x = 10

    def inner():
        print(x)

    return inner

f = outer()

f()
```

Output

```python
10
```

When `outer()` is called, Python creates a local variable `x`.

Normally, once `outer()` returns, its stack frame and local namespace are destroyed.

Since the returned function still depends on `x`, Python preserves only the required variables by attaching them to the returned function object's **closure**.

When `f()` is executed, Python first searches its local namespace.

Since `x` isn't found locally, Python looks inside the closure and finds `x = 10`.

---

## How Closures Work

```python
def outer():

    x = 10

    def inner():
        print(x)

    return inner

f = outer()
f()
```

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         1. outer() Starts Executing                        │
└────────────────────────────────────────────────────────────────────────────┘

                  Stack Frame : outer()

        +------------------------------------------------+
        | Local Namespace                                |
        |                                                |
        | x ───────────────────────────────► 10          |
        |                                                |
        | inner ───────────────────────┐                 |
        +------------------------------│-----------------+
                                       │
                                       ▼
                              Function Object
                             (inner function)


                           return inner
                               │
                               ▼


┌────────────────────────────────────────────────────────────────────────────┐
│                   2. outer() Finishes Executing                            │
└────────────────────────────────────────────────────────────────────────────┘

        outer() Stack Frame
        +-------------------------+
        | Destroyed               |
        +-------------------------+

                               │
                               ▼

                     f
                     │
                     ▼

          +--------------------------------------+
          | Function Object : inner              |
          |--------------------------------------|
          | Bytecode                             |
          | Parameters                           |
          | Closure                              |
          +------------------+-------------------+
                             │
                             ▼
                     x ─────────────► 10


Python preserves only the variables required by the returned function.
The original stack frame is gone.


┌────────────────────────────────────────────────────────────────────────────┐
│                         3. Calling f()                                     │
└────────────────────────────────────────────────────────────────────────────┘

                    f()

                     │
                     ▼

          Search for variable 'x'

             Local Namespace
                    │
          Not Found ❌
                    │
                    ▼
             Closure Variables
                    │
            Found x = 10 ✅
                    │
                    ▼
               print(10)


LEGB for a Closure

Local
   │
   ▼
Closure (Enclosing variables preserved by Python)
   │
   ▼
Global
   │
   ▼
Builtins
```

---

## Closures Store References, Not Copies

One important thing to understand is that closures **store references to variables**, not copies of their values.

```python
def outer():

    x = []

    def inner():
        x.append(1)
        return x

    return inner

f = outer()

print(f())
print(f())
print(f())
```

Output

```python
[1]
[1, 1]
[1, 1, 1]
```

The closure stores a reference to the same list object.

Every call to `inner()` modifies that same list.

Conceptually,

```
                Function Object

             +----------------------+
             | inner()              |
             |----------------------|
             | Closure              |
             +----------+-----------+
                        │
                        ▼
                  List Object
                  +-----------+
                  |    []     |
                  +-----------+
```

The list is never copied.

The closure simply remembers the same object.

---

## What Does a Closure Capture?

Another common interview question.

```python
def outer():

    x = 10

    def inner():
        print(x)

    x = 20

    return inner

f = outer()

f()
```

Output

```python
20
```

A closure captures the **variable**, not the value.

When `x` is updated before `outer()` returns, the closure still refers to the same variable.

By the time `inner()` executes, `x` contains `20`.

---

## Why Do We Need Closures?

Closures are useful whenever a function needs to remember some state after the outer function has finished executing.

They are widely used for:

- Decorators
- Function factories
- Callbacks
- Memoization
- Stateful functions

Decorators, which we'll study next, are built on top of closures.

---

## Examples

### Example 1

```python
def greeting(name):

    def greet():
        print(f"Hello {name}")

    return greet

say_hi = greeting("Gaurav")

say_hi()
```

Output

```python
Hello Gaurav
```

---

### Example 2

```python
def counter():

    count = 0

    def increment():

        nonlocal count

        count += 1

        return count

    return increment

c = counter()

print(c())
print(c())
print(c())
```

Output

```python
1
2
3
```

Notice that `count` is remembered between function calls.

---

## Follow-up Questions

### What is a closure?

A closure is a function object that remembers variables from its enclosing scope after the enclosing function has returned.

---

### Why are closures needed?

They allow functions to preserve state without using global variables.

---

### What does a closure store?

It stores references to the variables required by the inner function.

---

### Does a closure copy variables?

No.

It stores references to the original variables.

---

### Where are closure variables stored?

Inside the returned function object's closure.

---

### What is `nonlocal`?

`nonlocal` allows an inner function to modify a variable from its enclosing scope.

Without `nonlocal`, Python treats the variable as local to the inner function.

---

### How are closures different from nested functions?

Every closure is a nested function, but not every nested function is a closure.

A nested function becomes a closure only if it captures variables from its enclosing scope.

---

### Where are closures used in Python?

Closures are commonly used in decorators, callbacks, function factories, and stateful functions.

---

## Common Interview Mistakes

❌ Thinking the outer function's local namespace still exists.

✔ The stack frame is destroyed.

Only the required variables are preserved inside the closure.

---

❌ Thinking closures copy variables.

✔ Closures store references to variables.

---

❌ Thinking every nested function is a closure.

✔ A closure exists only when the inner function captures variables from the enclosing scope.

---

## Interview Tip

When asked about closures, avoid saying only:

> "A closure is a nested function."

A stronger answer is:

> "A closure is a function object that remembers variables from its enclosing scope even after the enclosing function has finished executing. Python achieves this by storing references to the required variables inside the function object's closure."

That demonstrates both conceptual understanding and knowledge of how Python implements closures.

---

## Key Takeaways

- A closure remembers variables from its enclosing scope.
- The outer function's stack frame is destroyed after it returns.
- Python preserves only the variables required by the returned function.
- Closures store references, not copies.
- Closures are the foundation of decorators.
- `nonlocal` allows modifying variables captured by a closure.
- Closures provide a clean way to maintain state without using global variables.

--- 

## How Decorators Use Closures

Decorators are one of the most common real-world applications of closures.

Consider a simple decorator.

```python
def logger(func):

    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)

    return wrapper
```

Notice what happens.

The outer function `logger()` receives a function object (`func`) as an argument.

The inner function `wrapper()` uses `func`, even after `logger()` has finished executing.

Normally, `func` would be destroyed when `logger()` returns.

Instead, Python preserves `func` inside the closure attached to `wrapper`.

Conceptually,

```
                logger(func)

                     │
                     ▼

            wrapper Function Object

          +---------------------------+
          | Bytecode                  |
          | Parameters                |
          | Closure                   |
          +-------------+-------------+
                        │
                        ▼
                 func ─────────────► say_hello()
```

When we later execute

```python
@logger
def say_hello():
    print("Hello")

say_hello()
```

Python actually executes

```python
wrapper()
```

The `wrapper` function still knows which function to execute because its closure remembers the reference to `func`.

This is why decorators work.

Without closures, the decorator would lose access to the original function as soon as `logger()` returned.