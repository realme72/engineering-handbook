# Property

## Why Do We Need Properties?

Suppose we have a simple class.

```python
class User:

    def __init__(self, age):

        self.age = age
```

Using it is straightforward.

```python
user = User(25)

print(user.age)
```

Output

```
25
```

Now suppose a new requirement arrives.

> A user's age should never be negative.

The simplest solution might be:

```python
class User:

    def set_age(self, age):

        if age < 0:
            raise ValueError("Invalid age")

        self.age = age
```

Now users must remember to write

```python
user.set_age(30)
```

instead of

```python
user.age = 30
```

The interface has changed.

This is exactly the problem that **properties** solve.

---

## What is a Property?

A **property** allows a method to be accessed like an attribute.

Instead of writing

```python
user.get_age()
```

we can simply write

```python
user.age
```

Even though Python is actually executing a method behind the scenes.

Properties let us add logic such as validation, computation, or lazy loading without changing how the attribute is accessed.

---

## Creating a Property

```python
class User:

    def __init__(self, age):

        self._age = age

    @property
    def age(self):

        return self._age
```

Usage

```python
user = User(25)

print(user.age)
```

Notice

```
user.age
```

not

```
user.age()
```

Although it looks like an attribute,

Python is actually calling a method.

Conceptually,

```
user.age

↓

age()

↓

return _age
```

---

## Why Use _age?

Notice we store

```python
self._age
```

instead of

```python
self.age
```

Why?

Suppose we wrote

```python
@property
def age(self):

    return self.age
```

Execution

```
age()

↓

return self.age

↓

age()

↓

return self.age

↓

Infinite Recursion
```

Eventually,

Python raises

```
RecursionError
```

The underscore is a naming convention indicating an internal attribute.

---

## Setter

Properties are not read-only.

We can define a setter.

```python
class User:

    def __init__(self, age):

        self._age = age

    @property
    def age(self):

        return self._age

    @age.setter
    def age(self, value):

        if value < 0:
            raise ValueError("Age cannot be negative")

        self._age = value
```

Usage

```python
user = User(25)

user.age = 30
```

Behind the scenes,

Python executes

```
age.setter()

↓

Validation

↓

Update _age
```

The caller still writes

```python
user.age = 30
```

No interface change.

---

## Getter + Setter Visualization

```
              user.age

                 │

        ┌────────┴────────┐

        ▼                 ▼

Read Attribute      Assign Attribute

        │                 │

   @property        @age.setter

        │                 │

     _age            Validate

                        │

                    Update _age
```

---

## Read-Only Property

Simply omit the setter.

```python
class Circle:

    def __init__(self, radius):

        self.radius = radius

    @property
    def area(self):

        return 3.14 * self.radius ** 2
```

Usage

```python
circle.area
```

Output

```
78.5
```

Trying

```python
circle.area = 100
```

raises

```
AttributeError
```

because no setter exists.

---

## Computed Properties

Properties are commonly used for derived values.

```python
class Rectangle:

    def __init__(self, length, width):

        self.length = length
        self.width = width

    @property
    def area(self):

        return self.length * self.width
```

The area is calculated whenever it's accessed.

No need to store duplicate data.

---

## Lazy Evaluation

Sometimes computing a value is expensive.

Instead of calculating it immediately,

calculate it only when needed.

```python
class Report:

    @property
    def data(self):

        print("Loading...")

        return load_from_database()
```

Nothing happens until

```python
report.data
```

is accessed.

---

## Why Properties Are Better Than Getters and Setters

Traditional OOP languages often use

```java
getAge()

setAge()
```

Python prefers

```python
user.age
```

because it is cleaner.

Internally,

properties still execute methods,

but users interact with them like normal attributes.

This makes APIs simpler while allowing validation and encapsulation.

---

## Real-World Examples

### Validation

```python
user.age = 30
```

The setter validates the input before updating the value.

---

### Computed Fields

```python
employee.salary_after_tax
```

Calculated whenever accessed.

---

### Lazy Loading

```python
image.data
```

The image file is loaded only when required.

---

### Read-Only Attributes

```python
person.full_name
```

Computed from

- first_name
- last_name

without allowing direct modification.

---

## Properties and Descriptors

Earlier we learned about

- Instance Methods
- Static Methods
- Class Methods

Properties are implemented using Python's **Descriptor Protocol**.

Conceptually,

```
Instance Method

↓

Descriptor


Static Method

↓

Descriptor


Class Method

↓

Descriptor


Property

↓

Descriptor
```

The Descriptor Protocol is the mechanism Python uses to customize attribute access.

You don't need to know its implementation details for most interviews, but it's useful to know that properties are built on top of it.

---

## Common Interview Questions

### What is a property?

A property allows a method to be accessed like an attribute. It provides a clean interface while still allowing logic such as validation or computation.

---

### Why use `@property` instead of getter methods?

Properties preserve a simple attribute-style interface (`user.age`) while allowing the implementation to include validation, lazy loading, or computed values.

---

### What is the purpose of `@property`?

It lets you control attribute access without changing how callers interact with the object.

---

### Why do we use `_age` instead of `age`?

Using `self.age` inside the property would recursively call the property again, resulting in infinite recursion. `_age` stores the actual value.

---

### What is a property setter?

A setter is a method decorated with `@property_name.setter` that runs whenever a value is assigned to the property, allowing validation or preprocessing.

---

### Can a property be read-only?

Yes. Simply define a getter without a setter.

---

### Are properties methods or attributes?

They are methods that behave like attributes. Python automatically invokes the underlying method when the property is accessed.

---

## Common Interview Mistakes

❌ Treating properties as ordinary variables.

✔ A property executes code whenever it is accessed.

---

❌ Using `self.age` inside the property getter.

✔ Store the actual value in a separate attribute such as `_age`.

---

❌ Writing `user.age()`.

✔ Properties are accessed like attributes, not methods.

---

## Interview Tip

If asked,

> **When would you use `@property`?**

A strong answer is:

> "I use properties when I want attribute-like access while still controlling how values are read or written. They're useful for validation, computed fields, lazy loading, and maintaining backward-compatible APIs."

---

## Key Takeaways

- A property makes a method behave like an attribute.
- `@property` defines the getter.
- `@property_name.setter` defines the setter.
- Properties enable validation, computation, and lazy loading.
- They preserve a clean attribute-based interface.
- Properties are implemented using Python's Descriptor Protocol.