# Class Methods

## What is a Class Method?

A **class method** is a method that operates on the class rather than a specific instance.

Unlike an instance method, Python automatically passes the **class** as the first argument, conventionally named `cls`.

Use a class method when the logic needs to work with class-level data or create new instances of the class.

---

## Creating a Class Method

Python provides the `@classmethod` decorator.

```python
class User:

    company = "Google"

    @classmethod
    def show_company(cls):

        print(cls.company)

User.show_company()
```

Output

```
Google
```

Python automatically passes the class as `cls`.

Conceptually,

```python
User.show_company()
```

becomes

```python
User.show_company(User)
```

---

## Understanding cls

`cls` is a reference to the class itself.

```
          User Class

              ▲

              │

             cls
```

Just as `self` refers to an object,

`cls` refers to the class.

---

## Memory Representation

```
               User Class

        company = "Google"

              │

              ▼

      show_company(cls)
```

Calling

```python
User.show_company()
```

binds the class.

```
User.show_company()

        │

        ▼

show_company(User)
```

Inside the method,

```
cls

        │

        ▼

User Class
```

---

## Why Do We Need Class Methods?

Suppose we want to create users from a string.

```python
class User:

    def __init__(self, name, age):

        self.name = name
        self.age = age
```

Without a class method,

```python
data = "Alice,25"

name, age = data.split(",")

user = User(name, int(age))
```

This parsing logic may be needed in multiple places.

Instead,

we can move it into the class.

---

## Factory Method

```python
class User:

    def __init__(self, name, age):

        self.name = name
        self.age = age

    @classmethod
    def from_string(cls, data):

        name, age = data.split(",")

        return cls(name, int(age))
```

Usage

```python
user = User.from_string("Alice,25")
```

The class method creates and returns a new object.

This is called a **factory method** or **alternative constructor**.

---

## Why Use cls Instead of User?

Notice we returned

```python
return cls(name, int(age))
```

instead of

```python
return User(name, int(age))
```

This supports inheritance.

Suppose

```python
class Admin(User):

    pass
```

Now,

```python
admin = Admin.from_string("Bob,30")
```

returns

```
Admin
```

not

```
User
```

Because

```
cls

↓

Admin
```

Using `cls` makes the method reusable across subclasses.

---

## Instance Method vs Static Method vs Class Method

### Instance Method

```
obj.method()

↓

self

↓

Object
```

---

### Static Method

```
Class.method()

↓

Nothing Passed
```

---

### Class Method

```
Class.method()

↓

cls

↓

Class
```

---

## When Should You Use a Class Method?

Use a class method when:

- Creating objects in different ways.
- Accessing or modifying class variables.
- Implementing factory methods.
- Writing behavior that belongs to the class rather than an individual object.

---

## Example

```python
class Employee:

    company = "Google"

    @classmethod
    def change_company(cls, name):

        cls.company = name

Employee.change_company("OpenAI")

print(Employee.company)
```

Output

```
OpenAI
```

The class variable changes for every instance.

---

## Real-World Examples

### from_json()

```python
user = User.from_json(data)
```

---

### from_dict()

```python
user = User.from_dict(payload)
```

---

### datetime.strptime()

```python
datetime.strptime(...)
```

Creates a `datetime` object from a formatted string.

---

### pathlib.Path.cwd()

Returns an instance of `Path`.

Many standard library APIs use class methods as alternative constructors.

---

## Common Interview Questions

### What is a class method?

A class method operates on the class instead of an instance. Python automatically passes the class as the first argument (`cls`).

---

### What is `cls`?

`cls` is a reference to the class itself. It is automatically passed whenever a class method is called.

---

### Why do we use `@classmethod`?

`@classmethod` is used when the method needs to access class-level data or create instances of the class without relying on an existing object.

---

### What is a factory method?

A factory method is a class method that creates and returns objects. It provides an alternative way to construct instances besides calling the constructor directly.

---

### Why use `cls` instead of the class name?

Using `cls` supports inheritance. If the method is called from a subclass, it automatically creates an instance of that subclass instead of the parent class.

---

### Can a class method access instance variables?

No.

A class method doesn't receive an instance, so it cannot directly access instance attributes.

---

### Can a class method access class variables?

Yes.

This is one of its primary use cases.

---

### Difference between instance, static, and class methods?

| Method | First Argument | Access Instance Data | Access Class Data |
|---------|---------------|----------------------|-------------------|
| Instance Method | `self` | ✅ | ✅ |
| Static Method | None | ❌ | Only explicitly |
| Class Method | `cls` | ❌ | ✅ |

---

## Common Interview Mistakes

❌ Using a class method when instance data is required.

✔ Use an instance method whenever object state is involved.

---

❌ Returning `User(...)` inside a class method.

✔ Return `cls(...)` to support inheritance.

---

❌ Thinking class methods belong to objects.

✔ Class methods operate on the class itself.

---

## Interview Tip

If asked,

> **When would you use a class method?**

A strong answer is:

> "I primarily use class methods to implement factory methods and alternative constructors. They're also useful when the logic operates on class-level data rather than a specific instance. Using `cls` instead of the class name makes the implementation inheritance-friendly."

---

## Key Takeaways

- Class methods operate on the class, not an instance.
- Python automatically passes the class as `cls`.
- Use `@classmethod` for factory methods and class-level operations.
- Prefer `cls(...)` over the class name to support inheritance.
- Class methods can access and modify class variables.
- They are commonly used as alternative constructors.

---


                    Python Methods

                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼

 Instance Method     Static Method      Class Method

      self                None               cls

       │                   │                 │

     Object             Utility          Class

       │                   │                 │

 Reads/Writes         Helper Logic      Factory Methods
 Instance State                         Class State

 Example:             Example:          Example:
 user.rename()        Math.add()        User.from_json()