# Strategy Pattern

## Intent

The Strategy Pattern is used when the same business operation can be performed in multiple ways and those implementations are expected to evolve over time.

Rather than embedding every variation inside a single class using conditional logic, each implementation is extracted into its own strategy. The client remains responsible for orchestrating the workflow, while the selected strategy becomes responsible for performing the actual work.

The primary goal of the Strategy Pattern is to isolate changing behavior so that new implementations can be introduced without modifying existing business logic.

### What does the pattern do?

It extracts interchangeable algorithms into separate classes and allows them to be selected dynamically at runtime.

### How does it work?

The client depends on an abstraction rather than a concrete implementation. Different strategies implement the same interface, allowing the client to switch between them without changing its own logic.

### What design problem does it solve?

It prevents classes from becoming filled with conditional logic (`if-else` or `switch` statements) when behavior varies based on runtime conditions.

---

## Why Was This Pattern Introduced?

Suppose you're building a payment service.

Initially, the application supports only credit card payments.

```python
class PaymentService:

    def pay(self, amount):

        process_credit_card(amount)
```

The implementation is simple.

A few weeks later, the business introduces UPI payments.

```python
if payment_type == "CARD":
    process_credit_card()

elif payment_type == "UPI":
    process_upi()
```

Soon afterwards, more payment methods are added.

- PayPal
- Apple Pay
- Stripe
- Razorpay

The implementation gradually becomes

```python
if payment_type == "CARD":
    ...

elif payment_type == "UPI":
    ...

elif payment_type == "PAYPAL":
    ...

elif payment_type == "APPLE":
    ...

elif payment_type == "STRIPE":
    ...
```

Every new payment method requires modifying the existing class.

This introduces several problems.

- The class grows continuously.
- Business logic becomes coupled with payment implementations.
- The class violates the Open/Closed Principle.
- Testing individual payment algorithms becomes more difficult.

The Strategy Pattern solves this by extracting each payment algorithm into its own class.

The payment service no longer knows how a payment is processed.

It simply delegates the request to the selected strategy.

---

## Real-World Analogy

Imagine using a navigation application.

You choose how you want to travel.

- Driving
- Walking
- Cycling
- Public Transport

The destination never changes.

Only the route calculation algorithm changes.

The navigation application doesn't contain one enormous method filled with route calculations.

Instead, it selects the appropriate routing strategy based on the user's choice.

---

## Software Engineering Example

A payment gateway is one of the best production examples.

Instead of writing

```text
Payment Service

↓

if Card

↓

if UPI

↓

if Stripe

↓

if Razorpay

↓

if PayPal
```

we separate every payment algorithm.

```text
Payment Service

↓

Payment Strategy

├── Credit Card

├── UPI

├── Stripe

├── Razorpay

└── PayPal
```

The payment service remains unchanged regardless of how many payment providers are introduced.

Other production examples include:

- Authentication (JWT, OAuth, API Key)
- Compression (ZIP, GZIP)
- Sorting Algorithms
- Tax Calculation
- Shipping Cost Calculation
- Retry Policies
- Cache Eviction Policies
- Serialization (JSON, XML, Protobuf)

---

## Python Implementation

```python
from abc import ABC, abstractmethod


class PaymentStrategy(ABC):

    @abstractmethod
    def pay(self, amount):
        pass


class CreditCardPayment(PaymentStrategy):

    def pay(self, amount):
        print(f"Paid ₹{amount} using Credit Card")


class UPIPayment(PaymentStrategy):

    def pay(self, amount):
        print(f"Paid ₹{amount} using UPI")


class PayPalPayment(PaymentStrategy):

    def pay(self, amount):
        print(f"Paid ₹{amount} using PayPal")


class PaymentService:

    def __init__(self, strategy):
        self.strategy = strategy

    def checkout(self, amount):
        self.strategy.pay(amount)


payment = PaymentService(UPIPayment())

payment.checkout(500)
```

**Output**

```text
Paid ₹500 using UPI
```

---

## Internal Workflow

When the client executes

```python
payment.checkout(500)
```

the following sequence occurs.

```text
Client

        │

        ▼

PaymentService

        │

Delegates

        ▼

PaymentStrategy

        │

────────┼──────────────

│        │           │

Card     UPI      PayPal

        │

        ▼

Process Payment
```

Notice that the payment service knows **when** a payment should be processed.

The strategy knows **how** it should be processed.

This separation allows both to evolve independently.

---

## How to Identify This Pattern

You are likely looking at a Strategy Pattern if you notice:

- Large `if-else` or `switch` statements selecting different algorithms.
- Multiple implementations of the same behavior.
- The client delegates work instead of implementing the algorithm itself.
- New algorithms can be added without modifying existing classes.

---

## Advantages

- ✅ Eliminates conditional logic.
- ✅ Follows the Open/Closed Principle.
- ✅ Encourages composition over inheritance.
- ✅ Makes algorithms independently testable.
- ✅ Simplifies introducing new business rules.

---

## Disadvantages

- ❌ Increases the number of classes.
- ❌ May introduce unnecessary abstraction for very simple logic.
- ❌ Clients must know which strategy to choose.

---

## When Should You Use It?

Use the Strategy Pattern when:

- Multiple algorithms solve the same problem.
- The algorithm should be selected at runtime.
- New algorithms are expected in the future.
- Large conditional statements are becoming difficult to maintain.

---

## When Should You Avoid It?

Avoid the Strategy Pattern when:

- Only one implementation exists.
- The algorithm is unlikely to change.
- The additional abstraction outweighs the benefit.

---

## Common Interview Questions

### Basic

- What problem does the Strategy Pattern solve?
- Why is Strategy better than large `if-else` statements?
- How does Strategy follow the Open/Closed Principle?

### Intermediate

- How is Strategy different from State?
- Why does Strategy encourage composition over inheritance?
- Can strategies be switched at runtime?

### Advanced

- Design a payment gateway using the Strategy Pattern.
- Where have you used Strategy in production?
- How would Dependency Injection improve a Strategy implementation?
- How would you unit test individual strategies?

---

## Interview Answer

### How would you explain the Strategy Pattern in an interview?

> The Strategy Pattern encapsulates interchangeable algorithms behind a common interface, allowing the appropriate implementation to be selected at runtime. Instead of embedding multiple variations of the same behavior inside a single class using conditional logic, each algorithm is implemented as an independent strategy. The client simply delegates the work to the selected strategy without knowing how it is implemented.
>
> I generally consider the Strategy Pattern whenever I see a class growing because of multiple `if-else` branches that implement different ways of solving the same problem. Extracting those algorithms into separate strategies keeps the client focused on orchestration while allowing new implementations to be introduced without modifying existing code.
>
> A common production example is a payment gateway. The checkout flow remains the same regardless of whether the customer pays using a credit card, UPI, Stripe, or PayPal. Each payment provider becomes a separate strategy implementing the same interface, allowing new providers to be added without changing the checkout service.

---

## Related Patterns

| Pattern | Difference |
|----------|------------|
| State | Strategy lets the client choose an algorithm. State changes behavior automatically based on the object's internal state. |
| Template Method | Template Method uses inheritance to vary parts of an algorithm. Strategy uses composition to replace the entire algorithm. |
| Bridge | Bridge separates abstraction from implementation. Strategy encapsulates interchangeable algorithms. |
| Command | Command encapsulates requests. Strategy encapsulates algorithms. |

---

## Strategy Resolution

The Strategy Pattern defines **how behavior is encapsulated**, but it does not prescribe **how a strategy should be selected**.

In production systems, strategies are typically resolved using:

- Dependency Injection (Spring, FastAPI)
- Registry Pattern
- Factory Pattern
- Configuration-based lookup

Avoid selecting strategies using large `if-else` or `switch` statements, as this simply relocates the conditional logic rather than eliminating it.

---

## Key Takeaways

- The Strategy Pattern encapsulates interchangeable algorithms behind a common interface.
- It eliminates large conditional statements by delegating behavior to independent strategy classes.
- The client focuses on orchestration while strategies focus on implementation.
- Strategy follows the Open/Closed Principle by allowing new algorithms to be introduced without modifying existing code.
- Payment gateways, authentication mechanisms, compression algorithms, retry policies, and shipping calculators are excellent production examples.