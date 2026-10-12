# Lambda Functions

## What is a Lambda Function?

A lambda is just another way to create a **function object**. We already know Python creates one every time it sees a `def`:

```python
def square(x):
    return x * x
```

If you only need that function once, Python lets you create the object right where you need it instead of naming a separate function:

```python
numbers = [1, 2, 3, 4]

result = list(
    map(lambda x: x * x, numbers)
)
```

People usually describe lambda as "an anonymous function," and that's true, but the more useful way to think about it is:

> **Lambda is just another way to create a function object.**

These two produce exactly the same kind of object:

```python
def square(x):
    return x * x
```

```python
lambda x: x * x
```

Proof:

```python
square = lambda x: x * x

print(type(square))
```

```python
<class 'function'>
```

There's no special "lambda object" hiding in there — it's a plain function object like any other.

---

## How Does It Work?

```python
def square(x):
    return x * x
```

Python creates a function object and binds it to `square`:

```
square
   │
   ▼
Function Object
```

Compare:

```python
lambda x: x * x
```

Same function object gets created — the only difference is that nothing points at it yet:

```
Function Object
```

Now:

```python
square = lambda x: x * x
```

It's tempting to think the lambda gets "named" `square` here. It doesn't. Just like `x = 10` doesn't rename the integer `10`, this line doesn't rename the lambda — it binds the name `square` to the function object that already exists:

```
square
   │
   ▼
Function Object
```

---

## Why Do We Need Lambda?

```python
def square(x):
    return x * x

numbers = [1, 2, 3, 4]

result = list(map(square, numbers))
```

This works fine, but `square()` only ever gets used once. Might as well skip naming it:

```python
numbers = [1, 2, 3, 4]

result = list(
    map(lambda x: x * x, numbers)
)
```

Lambda cuts out the boilerplate of naming a function you'll only ever call in one place.

---

## Why Can Lambda Only Have One Expression?

A frequent interview question. This isn't allowed:

```python
lambda x:
    print(x)
    return x * x
```

Lambda is built for small inline functions, on purpose. Once you need multiple statements, loops, exception handling, or actual business logic, reach for `def` instead. As a rule of thumb:

- Small expression → `lambda`
- Complex logic → `def`

---

## When Should You Use Lambda?

When the function is small, used once, and improves readability by staying inline:

```python
employees.sort(
    key=lambda employee: employee.salary
)
```

Much cleaner than writing a whole separate function just to return `employee.salary`.

---

## When Should You Use `def`?

When the function gets reused, spans more than one line, holds real business logic, or would just be clearer with a name attached to it. Instead of:

```python
square = lambda x: x * x
```

write:

```python
def square(x):
    return x * x
```

If a function deserves a name, give it one.

---

## Real-World Examples

### Sorting

```python
employees.sort(
    key=lambda employee: employee.salary
)
```

---

### Mapping

```python
numbers = [1, 2, 3, 4]

squares = list(
    map(lambda x: x * x, numbers)
)
```

---

### Filtering

```python
numbers = [1, 2, 3, 4, 5, 6]

evens = list(
    filter(lambda x: x % 2 == 0, numbers)
)
```

---

### Finding the Maximum

```python
employees = [
    {"name": "Alice", "salary": 90000},
    {"name": "Bob", "salary": 120000}
]

highest_paid = max(
    employees,
    key=lambda employee: employee["salary"]
)
```

---

## Examples

### Example 1

```python
square = lambda x: x * x

print(square(5))
```

Output

```python
25
```

---

### Example 2

```python
numbers = [1, 2, 3, 4]

result = list(
    map(lambda x: x * x, numbers)
)

print(result)
```

Output

```python
[1, 4, 9, 16]
```

---

### Example 3

```python
employees = [
    {"name": "Alice", "salary": 90000},
    {"name": "Bob", "salary": 120000}
]

employees.sort(
    key=lambda employee: employee["salary"]
)

print(employees)
```

Output

```python
[
    {'name': 'Alice', 'salary': 90000},
    {'name': 'Bob', 'salary': 120000}
]
```

---

## Follow-up Questions

### What is a lambda function?

An anonymous function used to create small function objects inline.

---

### Is lambda a different type of function?

No — it produces the same `function` object `def` does.

---

### Why do we use lambda?

To create small, one-off functions without writing a full `def` for them.

---

### Can lambda have multiple statements?

No — it's limited to a single expression.

---

### Can lambda return a value?

Yes — the expression's result is returned automatically.

---

### Is lambda faster than `def`?

No. Both produce the same kind of function object — lambda is just shorter syntax for it.

---

## Common Interview Mistakes

❌ Thinking lambda is a special type of function.

✔ It creates the same function object `def` does.

---

❌ Using lambda for complex business logic.

✔ Switch to `def` once the logic goes beyond a simple expression.

---

❌ Assigning lambdas to variables everywhere.

✔ If it deserves a name, use `def`.

---

## Interview Tip

Don't stop at:

> "Lambda is an anonymous function."

A stronger answer:

> "Lambda is another way to create a function object — the same `function` object `def` creates, just intended for short, inline functions used once. For anything reusable or more complex, I'd reach for `def`, since it's more readable and fits Python's style conventions better."

That answer signals actual understanding, not a memorized definition.

---

## Key Takeaways

- Lambda is another way to create a function object.
- It creates the same `function` object `def` does.
- It's intended for short, inline, single-use functions.
- It's limited to a single expression.
- Prefer `def` for anything reused or more complex.
- Lambda shows up constantly with `map()`, `filter()`, `sorted()`, and `max()`.
