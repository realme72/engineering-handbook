# Generators

## What is a Generator?

A generator is a special type of function that **produces one value at a time instead of returning all values at once**.

Unlike a normal function, a generator **pauses its execution after producing a value** and resumes from the same point when the next value is requested.

This makes generators extremely memory efficient for working with large datasets or infinite sequences.

---

## Why Do We Need Generators?

Suppose we want to generate one billion numbers.

A normal function would look like this.

```python
def get_numbers():

    numbers = []

    for i in range(1_000_000_000):
        numbers.append(i)

    return numbers
```

This creates a list containing **one billion integers** before returning it.

```
numbers

┌─────────────────────────────────────────────┐
│ 0 │ 1 │ 2 │ 3 │ ... │ 999999999 │
└─────────────────────────────────────────────┘

Entire list exists in memory.
```

This consumes a huge amount of memory.

Instead, a generator produces values only when they are requested.

```python
def get_numbers():

    for i in range(1_000_000_000):
        yield i
```

Now only one value exists at a time.

```
next(generator)

        │
        ▼

0

(next value isn't generated yet)
```

This is why generators are memory efficient.

---

## Generator Functions

A function becomes a generator as soon as it contains a `yield` statement.

```python
def numbers():

    yield 1
    yield 2
    yield 3
```

Calling the function **does not execute it**.

```python
gen = numbers()
```

Instead, Python creates a **generator object**.

```
gen
 │
 ▼
Generator Object
```

Nothing inside the function executes until `next()` is called.

---

## How `yield` Works

Consider the following example.

```python
def numbers():

    print("Start")
    yield 1

    print("Middle")
    yield 2

    print("End")
    yield 3
```

Calling the function

```python
gen = numbers()
```

prints nothing because the function hasn't started executing yet.

Now,

```python
next(gen)
```

Output

```text
Start
1
```

The generator executes until it reaches the first `yield`.

At `yield`, two things happen:

- The value is returned to the caller.
- The function pauses execution.

Execution resumes from the next line when `next()` is called again.

---

## How a Generator Works

```python
def numbers():

    print("Start")
    yield 1

    print("Middle")
    yield 2

    print("End")
    yield 3
```

```
Generator Function

print("Start")
      │
      ▼
yield 1  ◄────────────── Pauses here
      │
      ▼
print("Middle")
      │
      ▼
yield 2  ◄────────────── Pauses here
      │
      ▼
print("End")
      │
      ▼
yield 3  ◄────────────── Pauses here
      │
      ▼
Function Ends
      │
      ▼
StopIteration
```

Unlike `return`, `yield` does not terminate the function.

It simply pauses execution and preserves the current state.

---

## `yield` vs `return`

### `return`

```python
def foo():
    return 10
```

```
Function Starts
      │
      ▼
return 10
      │
      ▼
Function Ends
      │
      ▼
Stack Frame Destroyed
```

---

### `yield`

```python
def foo():
    yield 10
```

```
Function Starts
      │
      ▼
yield 10
      │
      ▼
Function Pauses
      │
      ▼
Execution State Preserved
      │
      ▼
next()
      │
      ▼
Function Resumes
```

This is the fundamental difference between `yield` and `return`.

---

## Calling `next()`

```python
def numbers():

    print("Start")
    yield 1

    print("Middle")
    yield 2

    print("End")
    yield 3

gen = numbers()

print(next(gen))
print(next(gen))
print(next(gen))
```

Output

```text
Start
1
Middle
2
End
3
```

Notice that execution resumes exactly after the previous `yield`.

The function never starts from the beginning again.

---

## What Happens After the Last `yield`?

```python
gen = numbers()

next(gen)
next(gen)
next(gen)
next(gen)
```

Output

```python
StopIteration
```

Once the generator reaches the end of the function:

- Execution completes.
- The stack frame is destroyed.
- The generator becomes exhausted.
- Every future call to `next()` raises `StopIteration`.

---

## Why Doesn't a `for` Loop Raise `StopIteration`?

Consider

```python
for value in numbers():
    print(value)
```

Internally, Python does something similar to this.

```python
gen = numbers()

while True:

    try:
        value = next(gen)
        print(value)

    except StopIteration:
        break
```

The `for` loop automatically catches the `StopIteration` exception and exits gracefully.

---

## Generator Expressions

Just like list comprehensions,

```python
squares = [x * x for x in range(5)]
```

Python also provides generator expressions.

```python
squares = (x * x for x in range(5))
```

The first creates a list.

The second creates a generator object.

```python
print(next(squares))
```

Output

```python
0
```

Generator expressions are commonly used when processing large datasets.

---

## Real-World Examples

### Reading Large Files

Instead of loading the entire file,

```python
with open("large.log") as f:
    for line in f:
        print(line)
```

Python reads one line at a time.

---

### Streaming Data

APIs often stream records one by one instead of loading everything into memory.

---

### Infinite Sequences

```python
def infinite():

    num = 0

    while True:
        yield num
        num += 1
```

The generator never stores all numbers.

It generates them on demand.

---

## Follow-up Questions

### What is a generator?

A generator is a function that produces values lazily using `yield`.

---

### What does `yield` do?

It returns a value and pauses execution while preserving the generator's state.

---

### Does calling a generator function execute it?

No.

It creates a generator object.

Execution starts only when `next()` is called.

---

### What is the difference between `yield` and `return`?

`return` terminates the function.

`yield` pauses execution and allows it to resume later.

---

### Why are generators memory efficient?

They generate values one at a time instead of storing the entire dataset in memory.

---

### What happens after the last `yield`?

The generator finishes execution and raises `StopIteration`.

---

### What is a generator expression?

A generator expression creates a generator object using parentheses instead of square brackets.

---

## Common Interview Mistakes

❌ Thinking a generator executes when it is called.

✔ Calling a generator function creates a generator object.

Execution begins only when `next()` is called.

---

❌ Thinking `yield` is the same as `return`.

✔ `yield` pauses execution.

`return` terminates the function.

---

❌ Thinking generators store all values.

✔ They generate values lazily on demand.

---

❌ Forgetting `StopIteration`.

✔ Every exhausted generator raises `StopIteration`.

---

## Interview Tip

A strong interview answer is:

> "A generator is a function that uses `yield` to produce values lazily. Calling the function creates a generator object instead of executing it. Every call to `next()` resumes execution from the previous `yield`, preserving the function's state. This allows generators to process very large datasets efficiently without loading everything into memory."

---

## Key Takeaways

- A generator produces values lazily.
- Calling a generator function creates a generator object.
- `yield` returns a value and pauses execution.
- The generator resumes from the previous `yield`.
- Only the current execution state is kept in memory.
- Generators are ideal for large datasets and streaming data.
- Exhausted generators raise `StopIteration`.
- `for` loops automatically handle `StopIteration`.