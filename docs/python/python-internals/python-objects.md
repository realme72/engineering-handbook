# What is a Python Object?

## Answer

A **Python object** is the fundamental building block of every Python program — every value that exists during execution is represented as one.

When people say **"everything is an object"** in Python, they mean it literally: an integer, a string, a list, a dict, a function, a class, a module — all of it is stored as an object in memory, following the same object model.

Every Python object has three fundamental properties:

- **Identity** – a unique identifier for the object.
- **Type** – the category or class it belongs to.
- **Value (State)** – the actual data it holds.

Variables themselves are **not objects**. They're just names (references) that point to objects.

---

## Explanation

A Python object is a runtime entity that bundles together **data** and **behavior**.

Unlike C, where primitives are treated differently from user-defined types, Python represents almost everything as an object. That uniform model is what makes the language consistent, and it's what enables dynamic typing, introspection, and first-class functions.

### Integers are Objects

```python
x = 10

print(type(x))
```

Output:

```python
<class 'int'>
```

`10` is an object of type `int`.

---

### Strings are Objects

```python
name = "Python"

print(type(name))
```

Output:

```python
<class 'str'>
```

`"Python"` is an object too.

---

### Lists are Objects

```python
numbers = [1, 2, 3]

print(type(numbers))
```

Output:

```python
<class 'list'>
```

The list is an object, and so is every element inside it.

---

### Dictionaries are Objects

```python
student = {
    "name": "John",
    "age": 22
}

print(type(student))
```

Output:

```python
<class 'dict'>
```

---

### Functions are Objects

```python
def greet():
    print("Hello")
```

Because functions are objects, you can:

Assign them to variables:

```python
func = greet
```

Pass them as arguments:

```python
def execute(fn):
    fn()
```

Return them from other functions:

```python
def get_function():
    return greet
```

That's the whole basis for Python's **first-class functions**.

---

### Classes are Objects

Even classes are objects.

```python
class Shape:
    pass

print(type(Shape))
```

Output:

```python
<class 'type'>
```

`Shape` is itself an object, created by the metaclass `type`.

---

## Every Python Object Has Three Fundamental Properties

### 1. Identity

Every object has a unique identity for its whole lifetime. You can check it with:

```python
x = 10

print(id(x))
```

In **CPython**, `id()` usually returns the object's memory address.

---

### 2. Type

Every object belongs to a specific type:

```python
print(type(10))
```

Output:

```python
<class 'int'>
```

The type determines which operations the object supports.

---

### 3. Value (State)

The value is the actual data stored inside the object.

```python
x = 10
```

This object has:

- Identity → a unique identifier
- Type → `int`
- Value → `10`

Another example:

```python
name = "Gaurav"
```

This object has:

- Identity → a unique identifier
- Type → `str`
- Value → `"Gaurav"`

---

## Variables are References, Not Objects

A common misconception is that variables store values. In Python, they store **references** to objects.

```python
x = 10
y = x
```

```
x ─────► Object (10)
          ▲
y ────────┘
```

Both variables point to the same integer object — the object exists independently of whatever names refer to it.

---

## Why is Everything an Object?

A single, uniform object model is what keeps Python simple and consistent. Because everything is an object:

- Functions can be passed as arguments.
- Functions can be returned from other functions.
- Classes can be assigned to variables.
- Objects can be inspected at runtime.
- Python supports dynamic typing.
- Python supports introspection.
- Python supports first-class functions.

---

## Diagram

```
                Python Object
          ┌─────────────────────────┐
          │                         │
          │      Identity           │
          ├─────────────────────────┤
          │                         │
          │        Type             │
          ├─────────────────────────┤
          │                         │
          │     Value / State       │
          └─────────────────────────┘
```

Example:

```
x ─────────────► Object
                ┌─────────────────────────┐
                │ Identity : 0x7FA32...   │
                │ Type     : int          │
                │ Value    : 10           │
                └─────────────────────────┘
```

---

## Examples

### Example 1: Everything is an Object

```python
x = 10
name = "Python"
nums = [1, 2, 3]

print(type(x))
print(type(name))
print(type(nums))
```

Output:

```
<class 'int'>
<class 'str'>
<class 'list'>
```

---

### Example 2: Functions are Objects

```python
def greet():
    print("Hello")

func = greet

func()
```

Output:

```
Hello
```

---

### Example 3: Classes are Objects

```python
class Person:
    pass

print(type(Person))
```

Output:

```
<class 'type'>
```

---

## Follow-up Questions

### What are the three properties of every Python object?

Identity, type, and value (state).

---

### Are variables objects?

No — they're references (names) that point to objects.

---

### Why are functions considered objects?

Because you can assign them to variables, pass them as arguments, and return them from other functions.

---

### Are classes objects?

Yes — they're objects created by the metaclass `type`.

---

### How do you get the identity of an object?

The built-in `id()` function.

---

### How do you determine an object's type?

The built-in `type()` function.

---

### Does every object occupy memory?

Yes. Every object exists somewhere in memory for its lifetime and stores its identity, type, and value there.

---

## Common Interview Mistakes

❌ Thinking only instances of user-defined classes are objects.

✔ Integers, strings, lists, dictionaries, functions, classes, and modules are all objects.

---

❌ Confusing variables with objects.

✔ Variables are references that point to objects.

---

❌ Assuming `id()` always returns the memory address.

✔ In **CPython**, it usually is, but other Python implementations can represent object identity differently.

---

❌ Believing objects only contain data.

✔ Every object has an identity, a type, and a value — and the type also determines what behavior (methods) is available on it.

---

## Key Takeaways

- Every runtime value in Python is an object.
- Integers, strings, lists, dictionaries, functions, classes, and modules are all objects.
- Every object has three fundamental properties:
  - Identity
  - Type
  - Value
- Variables are references to objects, not the objects themselves.
- Python's uniform object model enables dynamic typing, introspection, and first-class functions.
