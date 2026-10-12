# Abstract Factory Pattern

## Intent

The Abstract Factory Pattern provides an interface for creating
**families of related objects** without specifying their concrete
classes.

------------------------------------------------------------------------

## Why Was This Pattern Introduced?

Suppose you're building a cross-platform UI library.

``` python
button = WindowsButton()
checkbox = WindowsCheckbox()
```

Tomorrow you support macOS.

Now every place that creates UI components must change.

Problems:

-   Client depends on concrete classes.
-   Easy to accidentally mix Windows and macOS components.
-   Difficult to add support for new platforms.

Abstract Factory solves this by creating an entire family of related
objects through one factory.

------------------------------------------------------------------------

## Real-World Analogy

Imagine ordering furniture for a room. Pick the **Modern Collection**
and you get a matching sofa, table, and chair — not a Modern sofa
next to a Victorian chair.

------------------------------------------------------------------------

## Software Engineering Example

``` text
WindowsFactory
├── WindowsButton
└── WindowsCheckbox

MacFactory
├── MacButton
└── MacCheckbox
```

The client asks the factory for UI components without knowing their
concrete classes.

------------------------------------------------------------------------

## Python Implementation

``` python
from abc import ABC, abstractmethod

class Button(ABC):
    @abstractmethod
    def render(self): pass

class Checkbox(ABC):
    @abstractmethod
    def render(self): pass

class WindowsButton(Button):
    def render(self):
        print("Windows Button")

class WindowsCheckbox(Checkbox):
    def render(self):
        print("Windows Checkbox")

class GUIFactory(ABC):
    @abstractmethod
    def create_button(self): pass

    @abstractmethod
    def create_checkbox(self): pass

class WindowsFactory(GUIFactory):
    def create_button(self):
        return WindowsButton()

    def create_checkbox(self):
        return WindowsCheckbox()
```

------------------------------------------------------------------------

## How It Works Internally

    Client
      ↓
    Abstract Factory
      ↓
    Concrete Factory
      ↓
    Family of Related Objects

------------------------------------------------------------------------

## Advantages

-   Ensures compatible objects are created together.
-   Easy to switch entire product families.
-   Supports OCP and DIP.

## Disadvantages

-   More interfaces and classes.
-   Difficult to add a new product type.

## When Should You Use It?

-   Cross-platform UI
-   Database drivers
-   Cloud providers
-   Theme systems

## When Should You Avoid It?

-   Only one product family exists.
-   Products are unrelated.

## Common Interview Questions

### Basic

-   Difference between Factory Method and Abstract Factory?

### Intermediate

-   Why is it called a family of objects?

### Advanced

-   How would you implement it using Dependency Injection?

## Related Patterns

| Pattern | Difference |
| ------- | ---------- |
| Factory Method | Creates one object. |
| Builder | Builds one complex object. |

## Key Takeaways

-   Creates families of related objects.
-   Prevents incompatible object combinations.
-   Hides concrete implementations from the client.
