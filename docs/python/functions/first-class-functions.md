# Functions are First-Class Objects

In Python, **functions are first-class objects** — treated just like any other object (an integer, a string, a list). You can assign them to variables, pass them as arguments, return them from other functions, and stash them inside collections.

This is one of Python's more powerful features, and it's the foundation decorators, closures, callbacks, higher-order functions, and frameworks like Flask and FastAPI all build on.

---

## Everything in Python is an Object

We've already covered that almost everything in Python is an object:

```python
x = 10
```

```
x ─────────► int object (10)
```

```python
name = "Gaurav"
```

```
name ──────► str object ("Gaurav")
```

```python
numbers = [1, 2, 3]
```

```
numbers ───► list object
```

Functions follow the exact same rule.

---

## Functions are Objects

```python
def greet():
    print("Hello")
```

Running this creates a **function object**:

```
greet ─────────► Function Object
                     │
                     ├── Name
                     ├── Bytecode
                     ├── Parameters
                     ├── Default Arguments
                     └── Metadata
```

`greet` is just a name pointing at that object — confirm it yourself:

```python
def greet():
    print("Hello")

print(type(greet))
```

```python
<class 'function'>
```

---

## Functions Can Be Assigned to Variables

Since functions are objects, any variable can reference one.

```python
def greet():
    print("Hello")

say_hi = greet
```

```
greet ───────┐
             │
             ▼
        Function Object
             ▲
             │
say_hi ──────┘
```

Both names point at the same function, so calling either one runs it:

```python
say_hi()
```

```text
Hello
```

---

## Functions Can Be Passed as Arguments

Pass a function into another function without calling it.

```python
def greet():
    print("Hello")

def execute(func):
    func()

execute(greet)
```

Notice this passes `greet`, not `greet()` — the object itself, not the result of calling it.

```
greet ─────────► Function Object
                     ▲
                     │
                parameter func
```

Inside `execute()`, `func` just references that same object:

```text
Hello
```

---

## Functions Can Be Returned

A function can build and return another function.

```python
def outer():

    def inner():
        print("Hello")

    return inner
```

```python
f = outer()

f()
```

```text
Hello
```

`outer()` handed back a function object, and `f` now holds a reference to it.

---

## Functions Can Be Stored in Collections

In a list:

```python
def add():
    print("Add")

def delete():
    print("Delete")

operations = [add, delete]

operations[0]()
```

```text
Add
```

Or in a dict:

```python
routes = {
    "/add": add,
    "/delete": delete
}

routes["/add"]()
```

```text
Add
```

---

## Why Are They Called First-Class Objects?

Something qualifies as **first-class** if it can be assigned to a variable, passed as an argument, returned from a function, and stored in a collection. Functions check every box:

| Capability | Supported |
|------------|-----------|
| Assign to variables | ✅ |
| Pass as arguments | ✅ |
| Return from functions | ✅ |
| Store in lists | ✅ |
| Store in dictionaries | ✅ |

---

## Real-World Examples

### `sorted()`

```python
users = [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25},
]

sorted(users, key=lambda user: user["age"])
```

`key` takes a function directly.

---

### Callbacks

```python
def task():
    print("Task Executed")

def run(callback):
    callback()

run(task)
```

---

### Flask / FastAPI

```python
@app.get("/users")
def get_users():
    ...
```

Decorators receive a function object and return one.

---

### ThreadPoolExecutor

```python
executor.submit(task)
```

`task` gets passed around as an object here too.

---

## Examples

### Example 1

```python
def greet():
    print("Hello")

say_hi = greet

say_hi()
```

Output:

```text
Hello
```

---

### Example 2

```python
def greet():
    print("Hello")

def execute(func):
    func()

execute(greet)
```

Output:

```text
Hello
```

---

### Example 3

```python
def outer():

    def inner():
        print("Hello")

    return inner

f = outer()

f()
```

Output:

```text
Hello
```

---

### Example 4

```python
def add():
    print("Add")

operations = [add]

operations[0]()
```

Output:

```text
Add
```

---

## Follow-up Questions

### What is a first-class object?

One that can be assigned to a variable, passed as an argument, returned from a function, and stored in a collection.

---

### Why are functions called first-class objects?

Because they support every one of those operations, same as any other object.

---

### Are functions objects in Python?

Yes — Python creates a function object every time it executes a `def` statement.

---

### Can functions be passed to another function?

Yes, and without calling them — pass the name, not `name()`.

---

### Can functions return other functions?

Yes — a function can build and return a function object.

---

### Why is this feature useful?

It's what makes callbacks, decorators, closures, higher-order functions, and functional-style patterns possible in the first place.

---

## Common Interview Mistakes

❌ Thinking a function is just executable code.

✔ It's an object that bundles executable code together with metadata.

---

❌ Passing `greet()` instead of `greet`.

✔ `greet()` runs the function. `greet` passes the function object itself.

---

❌ Thinking only classes create objects.

✔ Functions are objects too.

---

## Key Takeaways

- Functions are objects in Python.
- Variables store references to function objects, same as with any other object.
- Functions can be assigned to variables, passed as arguments, and returned from other functions.
- Functions can be stored inside lists and dictionaries.
- First-class functions are the foundation decorators, closures, callbacks, and a lot of Python frameworks are built on.
