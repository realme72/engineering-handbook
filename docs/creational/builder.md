# Builder Pattern

## Intent

The Builder Pattern constructs a **complex object step by step**,
separating construction from representation.

------------------------------------------------------------------------

## Why Was This Pattern Introduced?

Imagine creating a `Computer` object.

``` python
computer = Computer(cpu, ram, gpu, storage, os, wifi, bluetooth)
```

As optional fields increase, constructors become unreadable.

Builder solves this by constructing objects incrementally.

------------------------------------------------------------------------

## Real-World Analogy

Ordering a burger.

You choose bun, patty, cheese, sauces, and toppings one by one.

The final burger is assembled after all choices are made.

------------------------------------------------------------------------

## Software Engineering Example

Building:

-   HTTP Requests
-   SQL Queries
-   Docker Images
-   Computer Configurations

------------------------------------------------------------------------

## Python Implementation

``` python
class Computer:

    def __init__(self):
        self.cpu = None
        self.ram = None
        self.storage = None

class ComputerBuilder:

    def __init__(self):
        self.computer = Computer()

    def add_cpu(self, cpu):
        self.computer.cpu = cpu
        return self

    def add_ram(self, ram):
        self.computer.ram = ram
        return self

    def build(self):
        return self.computer

computer = (ComputerBuilder()
            .add_cpu("Intel i9")
            .add_ram("32GB")
            .build())
```

------------------------------------------------------------------------

## How It Works Internally

    Builder
      ↓
    Configure Step-by-Step
      ↓
    build()
      ↓
    Final Object

## Advantages

-   Avoids telescoping constructors.
-   Readable object construction.
-   Supports immutable objects.

## Disadvantages

-   Additional builder class.
-   Overkill for simple objects.

## When Should You Use It?

-   Many optional fields.
-   Complex construction process.
-   Immutable objects.

## When Should You Avoid It?

-   Simple objects with few fields.

## Common Interview Questions

### Basic

-   Why Builder over constructors?

### Intermediate

-   Difference between Builder and Factory?

### Advanced

-   Fluent Builder vs Director?

## Related Patterns

| Pattern | Difference |
| ------- | ---------- |
| Factory Method | Chooses which object to create.|
Prototype | Clones an existing object.|

## Key Takeaways

-   Builds complex objects step by step.
-   Improves readability.
-   Separates construction from representation.
