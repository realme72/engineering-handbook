# Instance Methods

## What is an Instance Method?

An **instance method** is a method that operates on a specific object (instance) of a class.

It receives the instance as its first parameter, conventionally named `self`.

Because it has access to the object, an instance method can read and modify that object's state.

---

## A Simple Example

```python
class User:

    def greet(self):
        print("Hello")

user = User()

user.greet()
```

This looks straightforward.

But something interesting happens here.

The method definition is

```python
def greet(self):
```

which expects **one argument**.

Yet we call

```python
user.greet()
```

without passing anything.

So where did `self` come from?

---

## What Actually Happens?

When Python sees

```python
user.greet()
```

it automatically passes the instance.

Conceptually,

```python
User.greet(user)
```

Both are equivalent.

```
user.greet()

          │

          ▼

User.greet(user)
```

Python performs this method binding automatically.

---

## Understanding self

`self` is **not** a keyword.

It is simply the first parameter that receives the current object.

This works too.

```python
class User:

    def greet(me):

        print(me)
```

Although valid,

using anything other than `self` is strongly discouraged because `self` is the accepted Python convention.

---

## Memory Representation

```
                Class

              User

                 │

          greet(self)

                 │


------------------------------------


user

      │

      ▼

+-----------------------+

| name = "Gaurav"       |

| age = 25              |

+-----------------------+
```

Calling

```python
user.greet()
```

binds the object to the method.

```
user

        │

        ▼

greet(user)
```

Inside the method,

```
self

        │

        ▼

same object
```

Both `user` and `self` reference the same instance.

---

## Verifying It

```python
class User:

    def show(self):

        print(id(self))

user = User()

print(id(user))

user.show()
```

Output

```
140238974856400

140238974856400
```

Both IDs are identical.

This proves that `self` and `user` reference the same object.

---

## Why Do We Need self?

Suppose a class stores user information.

```python
class User:

    def __init__(self, name):

        self.name = name

    def greet(self):

        print(self.name)
```

Create two users.

```python
u1 = User("Alice")

u2 = User("Bob")
```

Calling

```python
u1.greet()
```

prints

```
Alice
```

Calling

```python
u2.greet()
```

prints

```
Bob
```

How does Python know which name to print?

Because `self` points to the instance that invoked the method.

Conceptually,

```
u1.greet()

↓

greet(u1)

↓

self = u1

↓

Alice
```

```
u2.greet()

↓

greet(u2)

↓

self = u2

↓

Bob
```

---

# Bound Methods

When we access

```python
user.greet
```

notice that we didn't call the method.

There are no parentheses.

```python
method = user.greet
```

What is stored inside `method`?

Let's check.

```python
print(type(method))
```

Output

```
<class 'method'>
```

Python creates a **bound method**.

A bound method is simply a method that already remembers which object it belongs to.

Conceptually,

```
user.greet

↓

Bound Method

↓

Function + user
```

It stores two things.

```
Bound Method

│

├── Function (greet)

└── Instance (user)
```

Now calling

```python
method()
```

is equivalent to

```python
User.greet(user)
```

The instance has already been remembered.

---

## Bound Method Visualization

```
          user

           │

           ▼

      Bound Method

      ┌──────────────┐

      │ greet()      │

      │ instance=user│

      └──────────────┘
```

Calling

```
method()
```

automatically supplies

```
self = user
```

---

## Accessing the Method from the Class

Now try

```python
User.greet
```

Notice the difference.

No object exists.

So Python returns the function itself.

```
User.greet

↓

Function Object
```

Calling

```python
User.greet()
```

raises an error.

```
TypeError

missing required positional argument 'self'
```

Because no instance was provided.

Instead,

```python
User.greet(user)
```

works perfectly.

---

## Instance Methods Can Access Instance Data

```python
class User:

    def __init__(self, name):

        self.name = name

    def rename(self, name):

        self.name = name
```

The method modifies the current object's state.

```
Before

user

↓

name = Alice


rename("Bob")


After

↓

name = Bob
```

---

## When Should You Use Instance Methods?

Use instance methods whenever the behavior depends on the state of a specific object.

Examples include:

- Updating account balance
- Changing user profile
- Validating object state
- Reading instance attributes

---

### Where are instance methods stored?

Instance methods are stored on the **class**, not on each object.

When accessed through an instance, Python creates a **bound method** that combines the function from the class with the current instance.

```
          User Class

        greet()

            │

            ▼

        Function Object

            ▲

            │

user.greet

↓

Bound Method

↓

Function + user
```

This design avoids storing a separate copy of every method for each object, making Python classes memory efficient.

## Common Interview Questions

### What is an instance method?

An instance method is a method that operates on a specific object. It automatically receives the instance as its first argument (`self`), allowing it to access and modify that object's state.

---

### What is `self`?

`self` is a reference to the current instance of the class. Python automatically passes it when an instance method is invoked through an object.

---

### Is `self` a keyword?

No. `self` is just a naming convention. You can technically use any name, but `self` is the universally accepted convention in Python.

---

### How is `self` passed automatically?

When you access a method through an instance, Python creates a **bound method**. The bound method stores the instance and automatically passes it as the first argument when invoked.

Conceptually,

```python
user.greet()
```

becomes

```python
User.greet(user)
```

---

### What is a bound method?

A bound method is a method object that remembers the instance it belongs to. When called, Python automatically supplies that stored instance as `self`.

---

### Why does `User.greet()` raise an error?

Because `greet()` expects an instance as its first argument. Calling it directly from the class doesn't provide `self`, so Python raises a `TypeError`.

Correct usage:

```python
User.greet(user)
```

---

### When should you use an instance method?

Use an instance method whenever the behavior depends on the state of a particular object. If the method needs to read or modify instance attributes, it should be an instance method.

---

### Can an instance method access class variables?

Yes. An instance method can access both instance variables and class variables through `self` or the class itself.

---

### Can an instance method be called without creating an object?

Yes, but you must explicitly pass an instance.

```python
user = User()

User.greet(user)
```

This is exactly what Python does internally when you write:

```python
user.greet()
```

---

### Why are methods defined inside the class instead of the object?

Methods represent behavior that is common to all instances of a class. Storing them on the class avoids duplicating the same function for every object, making memory usage more efficient.

---

## Common Interview Mistakes

❌ Thinking `self` is a keyword.

✔ It is simply the first parameter representing the current instance.

---

❌ Thinking Python creates a copy of the object for `self`.

✔ `self` references the exact same object.

---

❌ Thinking instance methods belong to the object.

✔ Methods are defined on the class.

Objects receive bound methods when accessed through an instance.

---

## Interview Tip

If asked,

> **How does Python automatically pass self?**

A strong answer is:

> "When an instance method is accessed through an object, Python creates a bound method. The bound method stores both the original function and the instance. When the bound method is invoked, Python automatically passes the stored instance as the first argument (`self`). Conceptually, `obj.method()` is equivalent to `Class.method(obj)`."

---

## Key Takeaways

- Instance methods operate on a specific object.
- `self` is a reference to the current instance.
- `self` is passed automatically by Python.
- `obj.method()` is conceptually equivalent to `Class.method(obj)`.
- Accessing a method through an instance creates a bound method.
- A bound method remembers both the function and the instance.
- Instance methods are used whenever behavior depends on object state.