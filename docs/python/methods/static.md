# Static Methods

## What is a Static Method?

A **static method** is a method that belongs to a class but does **not** operate on either the instance or the class itself.

Unlike instance methods, Python does **not** automatically pass `self`.

Unlike class methods, Python does **not** automatically pass `cls`.

A static method behaves like a regular function that happens to live inside a class.

---

## Why Do We Need Static Methods?

Consider a utility function.

```python
class Math:

    def add(a, b):
        return a + b
```

Calling

```python
Math.add(10, 20)
```

raises

```
TypeError

missing 1 required positional argument
```

Why?

Python assumes it's an instance method and expects `self`.

Since this method doesn't need an object,

we should declare it as a static method.

---

## Creating a Static Method

```python
class Math:

    @staticmethod
    def add(a, b):

        return a + b

print(Math.add(10, 20))
```

Output

```
30
```

Notice that neither `self` nor `cls` is passed.

---

## Can We Call It Using an Object?

Yes.

```python
math = Math()

print(math.add(10, 20))
```

Output

```
30
```

Even though it works,

the object is **not** passed automatically.

Conceptually,

```
math.add(10, 20)

↓

Math.add(10, 20)
```

The instance is ignored.

---

## Memory Representation

```
            Math Class

        @staticmethod

             add()

                 │

                 ▼

          Function Object
```

Unlike an instance method,

no bound method is created.

Python simply returns the original function.

---

## Instance Method vs Static Method

Instance method

```
user.greet()

↓

Bound Method

↓

self passed automatically
```

Static method

```
Math.add()

↓

Function

↓

Nothing passed automatically
```

---

## When Should You Use Static Methods?

Use a static method when the logic:

- Does not access instance variables.
- Does not access class variables.
- Logically belongs to the class.

Examples include:

- Validation
- Mathematical calculations
- String formatting
- Data conversion
- Utility helpers

---

## Example

```python
class User:

    @staticmethod
    def is_valid_age(age):

        return age >= 18

print(User.is_valid_age(20))
```

Output

```
True
```

Notice that this function has nothing to do with a particular user object.

It simply performs validation.

---

## Why Not Define a Normal Function?

You could write

```python
def is_valid_age(age):

    return age >= 18
```

outside the class.

A static method is useful when the function is closely related to the class conceptually.

For example,

```
User

├── create()

├── update()

├── delete()

└── is_valid_age()
```

Grouping related functionality improves readability.

---

## Common Interview Questions

### What is a static method?

A static method is a method that belongs to a class but does not receive either the instance (`self`) or the class (`cls`). It behaves like a regular function namespaced inside the class.

---

### Why do we use `@staticmethod`?

`@staticmethod` tells Python not to automatically pass `self` or `cls` when the method is called.

---

### Can a static method access instance variables?

No.

It doesn't receive an instance, so it cannot directly access instance attributes.

---

### Can a static method access class variables?

Not automatically.

It can access them only by explicitly referring to the class name.

```python
class User:

    role = "Admin"

    @staticmethod
    def get_role():

        return User.role
```

---

### Can a static method be called using an object?

Yes.

However, the object is not passed to the method.

```python
user = User()

user.method()

↓

User.method()
```

---

### When should you use a static method?

Use a static method when the logic is related to the class but doesn't depend on either instance state or class state.

---

### Where is a static method stored?

Like all methods, a static method is stored on the class.

Unlike an instance method, Python returns the original function instead of creating a bound method.

---

## Common Interview Mistakes

❌ Thinking static methods belong to objects.

✔ Static methods belong to the class.

---

❌ Thinking static methods receive `self`.

✔ Nothing is passed automatically.

---

❌ Using static methods for logic that accesses object state.

✔ Use instance methods whenever object state is required.

---

## Interview Tip

If asked,

> **When would you use a static method instead of an instance method?**

A strong answer is:

> "I'd use a static method when the functionality is conceptually related to the class but doesn't depend on instance or class state. Typical examples include validation, utility functions, parsing, and helper methods."

---

## Key Takeaways

- Static methods do not receive `self` or `cls`.
- They behave like regular functions defined inside a class.
- No bound method is created.
- They are useful for utility or helper functionality related to the class.
- Use `@staticmethod` whenever the method doesn't need access to object or class state.
