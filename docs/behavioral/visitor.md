# Visitor Pattern

## Intent

I use the Visitor Pattern whenever I have a stable object hierarchy but expect new operations to be added frequently.

If I notice the same set of classes repeatedly being modified every time a new feature is introduced, it's usually a sign that the operations should be moved out of those classes. Instead of embedding every new behavior inside the existing objects, I keep the object model focused on representing the domain and implement new functionality as separate visitor classes.

The primary goal of the Visitor Pattern is to make it easy to introduce new operations without modifying an existing object hierarchy.

### What does the pattern do?

It separates operations from the objects they operate on by moving those operations into dedicated visitor classes.

### How does it organize classes?

The pattern consists of four participants:

- **Element** – Declares the `accept()` method.
- **Concrete Elements** – Represent the object hierarchy.
- **Visitor** – Declares operations for every element type.
- **Concrete Visitors** – Implement specific operations.

### What design problem does it solve?

It prevents object classes from accumulating unrelated responsibilities while making it easy to introduce new operations without modifying existing classes.

---

# Why Was This Pattern Introduced?

Imagine you're building a compiler.

The compiler represents source code as an Abstract Syntax Tree (AST).

```
Program

↓

Function

↓

Expression

↓

Return
```

Each node is represented by a class.

```python
FunctionNode

ExpressionNode

VariableNode

ReturnNode
```

Initially, the AST only needs one feature.

Pretty Printing.

Someone writes

```python
class FunctionNode:

    def pretty_print(self):
        ...
```

Everything works.

---

A month later Product asks for

- Syntax Highlighting
- Type Checking
- Optimization
- Bytecode Generation
- Linting

Now every AST node starts growing.

```python
class FunctionNode:

    pretty_print()

    optimize()

    lint()

    generate_bytecode()

    type_check()
```

The same thing happens for

- VariableNode
- ExpressionNode
- ReturnNode

Soon every node becomes hundreds of lines long.

---

## The Real Problem

The AST is responsible for representing code.

It shouldn't also be responsible for:

- Printing
- Optimization
- Linting
- Code Generation
- Static Analysis

Those are completely different responsibilities.

Every new feature now requires modifying every AST node.

This violates the Open/Closed Principle.

---

## First Naive Solution

Move operations into helper functions.

```python
if isinstance(node, FunctionNode):
    ...

elif isinstance(node, VariableNode):
    ...

elif isinstance(node, ReturnNode):
    ...
```

This works.

Until you have

50 node types.

Every new operation now contains

50 `if-else` statements.

We're still modifying code every time.

---

## The Observation

The node already knows what type it is.

Instead of asking

```python
if isinstance(node, FunctionNode)
```

let the node decide.

Every node simply exposes

```python
accept(visitor)
```

The visitor contains the operation.

The node calls the correct visitor method automatically.

No `if`.

No `switch`.

No `isinstance`.

That observation leads to the Visitor Pattern.

---

# Real-World Analogy

Think about a hospital.

Patients don't perform their own operations.

The patient simply allows different specialists to examine them.

```
Patient

↓

Cardiologist

↓

Dentist

↓

Neurologist
```

The patient never changes.

Different specialists perform different operations.

Similarly,

the object hierarchy remains unchanged.

Different visitors perform different operations.

---

# Example 1 (Compiler / AST)

This is the classic production example.

```
Program

↓

Function

↓

Expression

↓

Return
```

Today you need

- Pretty Printing

Tomorrow

- Optimization

Later

- Code Generation

Later

- Static Analysis

Instead of modifying every node,

create visitors.

```
PrettyPrintVisitor

OptimizationVisitor

CodeGenerationVisitor

StaticAnalysisVisitor
```

The AST never changes.

Only new visitors are added.

---

# Example 2 (Shopping Cart Reporting)

Suppose every product implements

```python
accept(visitor)
```

Today you need

- Calculate Price

Tomorrow

- GST Calculation

Next month

- Discount Calculation

Later

- Export Invoice

Without Visitor,

every product class receives new methods.

With Visitor,

create

```
TaxVisitor

DiscountVisitor

InvoiceVisitor

ShippingCostVisitor
```

Products remain unchanged.

Only visitors grow.

---

# Python Implementation

```python
from abc import ABC, abstractmethod


# Visitor Interface
class Visitor(ABC):

    @abstractmethod
    def visit_book(self, book):
        pass

    @abstractmethod
    def visit_laptop(self, laptop):
        pass


# Element Interface
class Product(ABC):

    @abstractmethod
    def accept(self, visitor):
        pass


class Book(Product):

    def __init__(self, price):
        self.price = price

    def accept(self, visitor):
        visitor.visit_book(self)


class Laptop(Product):

    def __init__(self, price):
        self.price = price

    def accept(self, visitor):
        visitor.visit_laptop(self)


class TaxVisitor(Visitor):

    def visit_book(self, book):
        print(f"Book Tax = {book.price * 0.05}")

    def visit_laptop(self, laptop):
        print(f"Laptop Tax = {laptop.price * 0.18}")


products = [
    Book(1000),
    Laptop(50000)
]

visitor = TaxVisitor()

for product in products:
    product.accept(visitor)
```

Output

```
Book Tax = 50.0

Laptop Tax = 9000.0
```

---

# Internal Workflow

The Visitor Pattern consists of four participants.

```text
                    Visitor
                       ▲
                       │
             visitBook(Book)
             visitLaptop(Laptop)

+-------------------------------+
|         TaxVisitor            |
+-------------------------------+

           ▲               ▲
           │               │
      accept()         accept()

+------------+     +--------------+
|    Book    |     |   Laptop     |
+------------+     +--------------+
```

### Responsibilities

**Element (Book, Laptop)**

- Represents the domain object.
- Exposes the `accept(visitor)` method.
- Delegates the operation to the visitor.

---

**Visitor**

- Declares operations for every element type.
- Knows how to process each object.

---

**Concrete Visitor**

- Implements a specific business operation.
- Can be replaced with another visitor without changing the object hierarchy.

---

Notice something important.

The Product classes never calculate tax.

They simply allow the visitor to perform the operation.

This keeps business operations separate from the domain model.

---

# How It Works Internally

Suppose we execute

```python
product.accept(visitor)
```

If

```python
product = Book()
```

then internally

```
Book.accept(visitor)

↓

visitor.visit_book(book)
```

If

```python
product = Laptop()
```

then

```
Laptop.accept(visitor)

↓

visitor.visit_laptop(laptop)
```

The client never performs

```python
isinstance(product, Book)
```

or

```python
if product.type == ...
```

The correct method is selected automatically through **double dispatch**.

---

## What is Double Dispatch?

Normally,

Python uses **single dispatch**.

```python
obj.method()
```

The method executed depends only on

```
obj
```

With Visitor,

the operation depends on

- The object type
- The visitor type

Example

```
Book

+

TaxVisitor

↓

visit_book()
```

Later

```
Book

+

DiscountVisitor

↓

visit_book()
```

Same object.

Different visitor.

Different behavior.

That's why Visitor is sometimes described as using **double dispatch**.

---

# How to Identify This Pattern

You are likely looking at the Visitor Pattern if you notice:

- A stable object hierarchy.
- New business operations being added frequently.
- The same object classes repeatedly modified whenever a new feature is introduced.
- Methods like

```python
accept(visitor)
```

- Visitors containing methods like

```python
visit_book()

visit_order()

visit_customer()
```

---

# Advantages

- ✅ Easy to introduce new operations.
- ✅ Keeps domain objects focused on representing data.
- ✅ Follows the Open/Closed Principle for new operations.
- ✅ Eliminates large `if-else` or `isinstance` chains.
- ✅ Related business logic stays grouped inside one visitor.

---

# Disadvantages

- ❌ Adding a new element requires updating every visitor.
- ❌ Can introduce many visitor classes.
- ❌ Adds extra abstraction.
- ❌ Overkill for small object hierarchies.

---

# When Should You Use It?

Use Visitor when:

- The object hierarchy is relatively stable.
- New operations are introduced frequently.
- Business logic should remain separate from the domain model.

Examples:

- Compiler AST
- Query Planners
- Expression Trees
- Shopping Cart Reports
- Invoice Generation
- Static Analysis Tools

---

# When Should You Avoid It?

Avoid Visitor when:

- New element types are added frequently.
- The object hierarchy changes often.
- Only one or two operations exist.
- Simplicity is more important than extensibility.

---

# Common Interview Questions

## Basic

- What problem does the Visitor Pattern solve?
- Why not simply add methods to existing classes?
- What is the purpose of `accept()`?

---

## Intermediate

- What is Double Dispatch?
- Why is Visitor useful for compilers?
- What happens when a new element is introduced?

---

## Advanced

- Design an AST using the Visitor Pattern.
- How would you implement code generation using Visitor?
- Why do compilers heavily use the Visitor Pattern?
- Would you use Visitor in a microservice architecture?

---

# Interview Answer

> I use the Visitor Pattern when I have a stable object hierarchy but expect new business operations to be introduced regularly. Rather than modifying every class whenever a new operation is required, I keep the domain model focused on representing the business entities and move new behavior into visitor implementations. This allows new functionality to be added without changing the existing object hierarchy. A compiler's Abstract Syntax Tree is one of the best production examples, where operations such as optimization, type checking, code generation, and pretty printing evolve independently while the AST structure remains relatively stable.

---

# Visitor vs Strategy

This is a very common interview question.

Although both patterns encapsulate behavior, they solve different problems.

| Pattern | Focus | Typical Use |
|----------|-------|-------------|
| **Strategy** | Choose one algorithm | Payment Methods, Sorting, Compression |
| **Visitor** | Add new operations | AST, Reports, Query Planners |

### Strategy

The client chooses one implementation.

```python
PaymentService(CardPayment())
```

Tomorrow

```python
PaymentService(UPIPayment())
```

The algorithm changes.

The object hierarchy does not.

---

### Visitor

The object hierarchy stays the same.

```
Book

Laptop

Phone
```

Tomorrow

add

```
TaxVisitor
```

Next month

```
DiscountVisitor
```

Next month

```
InvoiceVisitor
```

The operations change.

The object hierarchy does not.

---

# Visitor vs Template Method

Template Method defines

one algorithm

where certain steps vary.

Visitor introduces

entirely new operations

without modifying existing classes.

---

# Related Patterns

| Pattern | Difference |
|----------|------------|
| Strategy | Strategy selects one algorithm. Visitor adds entirely new operations. |
| Template Method | Template Method varies steps in one algorithm. Visitor introduces new algorithms altogether. |
| Composite | Composite builds object hierarchies. Visitor performs operations on those hierarchies. |
| Iterator | Iterator traverses a structure. Visitor performs operations on its elements. |

---

# Key Takeaways

- Visitor is best suited for stable object hierarchies.
- New operations are implemented as new visitor classes.
- Domain objects remain focused on representing business entities.
- `accept(visitor)` eliminates large `if-else` and `isinstance` chains.
- Compilers, ASTs, expression trees, and query planners are the strongest production examples.
- Visitor follows the Open/Closed Principle for adding new operations but makes adding new element types more expensive.