# Factory Method Pattern

## Intent

Factory Method defines an interface for creating objects, but lets
subclasses decide which concrete object actually gets instantiated.

Instead of calling a constructor directly, the client delegates
creation to a factory method — which loosens the coupling between
business logic and specific implementations.

------------------------------------------------------------------------

## Why Was This Pattern Introduced?

Take a payment service:

``` python
class PaymentService:

    def process_payment(self, payment_type):

        if payment_type == "credit":
            payment = CreditCardPayment()

        elif payment_type == "paypal":
            payment = PayPalPayment()

        elif payment_type == "upi":
            payment = UPIPayment()

        payment.pay()
```

Initially, this works well.

As the application grows, new payment methods are introduced:

-   Stripe
-   Apple Pay
-   Google Pay
-   Crypto

Every new payment type requires modifying `PaymentService`.

Problems with this approach:

-   Business logic is tightly coupled with object creation.
-   Violates the Single Responsibility Principle.
-   Violates the Open/Closed Principle.
-   Difficult to test because dependencies are created internally.

The Factory Method Pattern solves this by moving object creation into
dedicated creator classes.

------------------------------------------------------------------------

## Real-World Analogy

Think of ordering food at a restaurant.

You tell the waiter what you want — you don't walk into the kitchen
and cook it yourself. The kitchen decides who prepares it and how.

Business logic works the same way: it requests an object instead of
creating one directly.

------------------------------------------------------------------------

## Software Engineering Example

Take a notification service.

Without Factory Method:

``` python
if notification_type == "email":
    sender = EmailSender()
elif notification_type == "sms":
    sender = SmsSender()
elif notification_type == "push":
    sender = PushSender()

sender.send()
```

Every new channel means touching existing code.

With Factory Method, separate creator classes return the right
sender, and the workflow itself never has to change.

------------------------------------------------------------------------

## Python Implementation

``` python
from abc import ABC, abstractmethod

class Payment(ABC):

    @abstractmethod
    def pay(self):
        pass


class CreditCardPayment(Payment):

    def pay(self):
        print("Paid using Credit Card")


class PayPalPayment(Payment):

    def pay(self):
        print("Paid using PayPal")


class PaymentCreator(ABC):

    @abstractmethod
    def create_payment(self):
        pass

    def checkout(self):
        payment = self.create_payment()
        payment.pay()


class CreditCardCreator(PaymentCreator):

    def create_payment(self):
        return CreditCardPayment()


class PayPalCreator(PaymentCreator):

    def create_payment(self):
        return PayPalPayment()
```

Client:

``` python
creator = CreditCardCreator()
creator.checkout()
```

------------------------------------------------------------------------

## How It Works Internally

    Client

    ↓

    checkout()

    ↓

    create_payment()

    ↓

    Concrete Product

    ↓

    payment.pay()

The client never directly creates a concrete object.

------------------------------------------------------------------------

## Code Walkthrough

### Why create a Product interface?

The client depends on `Payment` instead of concrete classes like
`CreditCardPayment` or `PayPalPayment`.

### Why is `create_payment()` abstract?

Each subclass decides which object should be created.

### Why is `checkout()` implemented in the base class?

The workflow is common. Only object creation varies.

------------------------------------------------------------------------

## Advantages

-   Decouples object creation from business logic.
-   Supports the Open/Closed Principle.
-   Easier to extend with new implementations.
-   Improves testability.
-   Encourages programming to abstractions.

------------------------------------------------------------------------

## Disadvantages

-   Introduces additional classes.
-   Slightly increases code complexity.
-   Can be unnecessary for very small applications.

------------------------------------------------------------------------

## When Should You Use It?

Use Factory Method when:

-   Object creation varies.
-   New implementations are added frequently.
-   Business logic should not depend on concrete classes.

Examples:

-   Payment gateways
-   Notification providers
-   Database connectors
-   File parsers
-   Cloud storage providers

------------------------------------------------------------------------

## When Should You Avoid It?

Avoid Factory Method when:

-   Only one implementation exists.
-   Object creation is straightforward.
-   A simple constructor or helper function is sufficient.

------------------------------------------------------------------------

## Common Interview Questions

### Basic

-   What problem does Factory Method solve?
-   How is it different from directly calling a constructor?

### Intermediate

-   Which SOLID principles does Factory Method support?
-   Why is the factory method abstract?

### Advanced

-   Factory Method vs Simple Factory?
-   Factory Method vs Abstract Factory?
-   Factory Method vs Dependency Injection?

------------------------------------------------------------------------

## Related Patterns

| Pattern | Difference |
| ------- | ---------- |
| Singleton | Singleton controls how many instances exist. Factory Method controls which object is created.|
| Abstract Factory | Creates families of related objects. Factory Method creates one product.|
| Builder | Builder constructs complex objects step by step. Factory Method chooses the object to instantiate.|

## Key Takeaways

-   Factory Method separates object creation from business logic.
-   The client depends on abstractions, not concrete implementations.
-   It primarily supports SRP, OCP, and DIP.
-   It is useful when new implementations are expected over time.
