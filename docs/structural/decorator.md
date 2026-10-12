# Decorator Pattern

## Intent

Decorator adds new behavior to an object at runtime, without touching its original implementation.

Instead of changing the existing class, you wrap the original object inside one or more decorator objects. Each one keeps the original interface intact, adding its own work before or after passing the call along to whatever it wraps.

### What does the pattern do?

It wraps an existing object with another object that adds new functionality while preserving the same interface.

### How does it work?

The client interacts with the decorator instead of the original object. The decorator performs additional work before or after delegating the request to the wrapped object.

Multiple decorators can be stacked together, allowing behaviors to be composed dynamically.

### What structural problem does it solve?

It allows behavior to be extended without modifying existing classes. This avoids creating large monolithic classes with multiple responsibilities and follows the Open/Closed Principle.

---

## Why Was This Pattern Introduced?

Take a payment service.

At first it only processes payments.

```python
payment.pay(1000)
```

As the application evolves, new requirements appear.

- Authenticate the user.
- Log every payment.
- Retry failed payments.
- Collect metrics.
- Audit every transaction.

A naive implementation keeps adding responsibilities to the same class.

```python
class PaymentService:

    def pay(self, amount):

        authenticate()

        log()

        metrics()

        retry()

        audit()

        print(f"Paid ₹{amount}")
```

This class gets harder to test and maintain with every feature you bolt on.

And every new feature means touching code that already works — which is how bugs creep in.

Decorator fixes this by giving each responsibility its own wrapper instead of cramming it into `PaymentService`.

```text
PaymentService

↓

LoggingDecorator

↓

AuthenticationDecorator

↓

RetryDecorator
```

Each decorator has a single responsibility and can be added or removed independently.

---

## Real-World Analogy

Imagine ordering a coffee.

Initially you order:

```text
Coffee
```

Later you decide to add milk.

```text
Coffee + Milk
```

Then sugar.

```text
Coffee + Milk + Sugar
```

Then whipped cream.

```text
Coffee + Milk + Sugar + Whipped Cream
```

The original coffee never changes.

Each topping simply wraps the previous coffee and adds additional behavior.

Decorator works exactly the same way.

---

## Software Engineering Example

One of the best production examples is **FastAPI Middleware**.

A request enters the application.

```text
Incoming Request

↓

Authentication Middleware

↓

Logging Middleware

↓

Rate Limiting Middleware

↓

Metrics Middleware

↓

Business Logic

↓

Response
```

Each middleware wraps the next one.

Every middleware performs additional work before or after calling:

```python
await call_next(request)
```

The route handler never changes.

New middleware can be added or removed independently without modifying business logic.

Other real-world examples include:

- Django Middleware
- Express Middleware
- Spring Filters
- ASP.NET Middleware
- Logging Frameworks
- Retry Libraries
- Caching Layers

---

## Python Implementation

```python
from abc import ABC, abstractmethod


class PaymentService(ABC):

    @abstractmethod
    def pay(self, amount):
        pass


class BasicPaymentService(PaymentService):

    def pay(self, amount):
        print(f"Paid ₹{amount}")


class PaymentDecorator(PaymentService):

    def __init__(self, payment_service):
        self.payment_service = payment_service


class LoggingDecorator(PaymentDecorator):

    def pay(self, amount):
        print("Logging payment...")
        self.payment_service.pay(amount)


class AuthenticationDecorator(PaymentDecorator):

    def pay(self, amount):
        print("Authenticating user...")
        self.payment_service.pay(amount)


payment = AuthenticationDecorator(
            LoggingDecorator(
                BasicPaymentService()
            )
         )

payment.pay(1000)
```

**Output**

```text
Authenticating user...
Logging payment...
Paid ₹1000
```

---

## Internal Workflow

When the client executes

```python
payment.pay(1000)
```

the following sequence occurs.

```text
Client

        │

        ▼

AuthenticationDecorator

        │

Adds Authentication

        ▼

LoggingDecorator

        │

Adds Logging

        ▼

BasicPaymentService

        │

Processes Payment

        ▼

Response
```

Every decorator follows the same sequence.

1. Receive the request.
2. Perform its additional behavior.
3. Delegate the request to the wrapped object.
4. Return the result.

Each decorator remains independent of every other decorator.

---

## How to Identify This Pattern

You are likely looking at a Decorator Pattern if you notice:

- Objects wrapping other objects of the same interface.
- Additional behavior added before or after delegating a request.
- Multiple wrappers stacked together.
- Existing classes remaining unchanged while new functionality is added dynamically.

---

## Advantages

- ✅ Adds new behavior without modifying existing classes.
- ✅ Supports the Open/Closed Principle.
- ✅ Promotes Single Responsibility Principle.
- ✅ Behaviors can be combined dynamically.
- ✅ Individual decorators remain small and reusable.

---

## Disadvantages

- ❌ Introduces many small classes.
- ❌ Debugging becomes harder with multiple nested decorators.
- ❌ Object creation becomes more complex.
- ❌ Order of decorators can affect behavior.

---

## When Should You Use It?

Use the Decorator Pattern when:

- You want to add responsibilities dynamically.
- You want to avoid modifying existing classes.
- Different combinations of behavior are required.
- Features should be reusable and independently configurable.

---

## When Should You Avoid It?

Avoid the Decorator Pattern when:

- Only a single behavior will ever exist.
- The added abstraction outweighs the benefits.
- Simpler inheritance is sufficient.
- Too many decorators make the code difficult to understand.

---

## Common Interview Questions

### Basic

- What problem does the Decorator Pattern solve?
- How is it different from inheritance?
- Why does every decorator implement the same interface?

### Intermediate

- How does the Decorator Pattern follow the Open/Closed Principle?
- Why is FastAPI Middleware considered a Decorator Pattern?
- Can decorators be combined?

### Advanced

- How is the Decorator Pattern different from Proxy?
- How is the Decorator Pattern different from Adapter?
- How would you implement retry, logging, and metrics using decorators?

---

## Related Patterns

| Pattern | Difference |
|----------|------------|
| Adapter | Adapter changes an object's interface. Decorator preserves the interface while adding behavior. |
| Proxy | Proxy controls access to an object. Decorator extends an object's behavior. |
| Facade | Facade simplifies a subsystem. Decorator enhances an individual object. |
| Composite | Composite represents part-whole hierarchies. Decorator wraps a single object to add functionality. |

---

## Key Takeaways

- The Decorator Pattern adds behavior dynamically without modifying existing classes.
- Every decorator preserves the same interface as the object it wraps.
- Multiple decorators can be composed together to build complex behavior.
- FastAPI, Django, Express, and Spring middleware are excellent real-world examples.
- Decorator emphasizes **extending behavior**, not changing interfaces.