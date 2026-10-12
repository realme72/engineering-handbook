# Adapter Pattern

## Intent

Adapter lets classes with incompatible interfaces work together by introducing an object that translates one interface into another.

Neither the client nor the existing class changes — the adapter sits between them as a bridge. The client keeps using the interface it already knows, and the adapter forwards the call to the right method on the underlying object.

#### What does the pattern do?

It introduces an adapter object that implements the interface expected by the client and translates requests into the interface provided by an existing class.

#### How does it work?

It introduces an intermediate adapter object between the client and the existing class. The client interacts only with the adapter, while the adapter delegates requests to the underlying object.

#### What structural problem does it solve?

It enables classes with incompatible interfaces to collaborate without modifying either the client or the existing implementation. This makes the system easier to extend and allows new integrations to be added with minimal changes to existing code.

---

## Why Was This Pattern Introduced?

Say an e-commerce app starts out integrated only with Stripe.

The application expects every payment provider to expose the following interface:

```python
payment_provider.pay(amount)
```

Stripe conveniently provides a compatible API:

```python
stripe.pay(amount)
```

Later, the business wants Razorpay too. But Razorpay exposes a different interface:

```python
razorpay.make_payment(amount)
```

Now there are two incompatible interfaces to deal with, and the naive fix is conditional logic scattered through the codebase.

```python
if provider == "stripe":
    stripe.pay(amount)

elif provider == "razorpay":
    razorpay.make_payment(amount)

elif provider == "paypal":
    paypal.send_money(amount)
```

As new providers are added:

- Business logic becomes tightly coupled to third-party SDKs.
- Every new integration requires modifying existing code.
- The application becomes harder to maintain and test.
- The code violates the Open/Closed Principle.

Adapter fixes this with a translation layer between the app and each external library.

The application continues to call:

```python
payment_provider.pay(amount)
```

while each adapter translates the request into the API expected by its respective provider.

---

## Real-World Analogy

Think of an Indian traveler in Europe. Their laptop charger has an Indian plug; European sockets are a different shape.

Nobody rewires the charger or replaces the sockets — they just use a travel adapter.

```text
Laptop Charger
        │
        ▼
Travel Adapter
        │
        ▼
European Socket
```

Neither the laptop nor the socket changes — the adapter just converts one interface into the other. Same idea in software.

---

## Software Engineering Example

Integrating multiple payment gateways is one of the most common real uses of this pattern.

Say your app defines one common interface.

```python
payment_provider.pay(amount)
```

Different payment providers expose different APIs.

```python
Stripe
-------
pay(amount)

Razorpay
---------
make_payment(amount)

PayPal
-------
send_money(amount)
```

Instead of forcing the application to understand every SDK, an adapter is written for each provider.

```text
Application
        │
        ▼
Payment Interface
        │
 ┌──────┴─────────┐
 ▼                ▼
StripeAdapter   RazorpayAdapter
      │                │
      ▼                ▼
 Stripe SDK      Razorpay SDK
```

Business logic stays completely independent of any specific SDK.

Adding a new provider just means writing another adapter.

---

## Python Implementation

```python
from abc import ABC, abstractmethod


class PaymentProvider(ABC):

    @abstractmethod
    def pay(self, amount):
        pass


class Razorpay:

    def make_payment(self, amount):
        print(f"Paid ₹{amount} using Razorpay")


class RazorpayAdapter(PaymentProvider):

    def __init__(self, razorpay):
        self.razorpay = razorpay

    def pay(self, amount):
        self.razorpay.make_payment(amount)


client = RazorpayAdapter(Razorpay())
client.pay(1000)
```

**Output**

```text
Paid ₹1000 using Razorpay
```

---

## Internal Workflow

Calling

```python
client.pay(1000)
```

triggers this sequence.

```text
Client

        │

        ▼

PaymentProvider.pay()

        │

        ▼

RazorpayAdapter.pay()

        │

Delegates request

        ▼

Razorpay.make_payment()

        │

        ▼

Payment Successful
```

The client never interacts directly with the Razorpay SDK.

Instead:

1. The client calls the interface it already understands.
2. The adapter receives the request.
3. The adapter translates the request into the appropriate SDK call.
4. The third-party library performs the actual work.
5. The result is returned to the client.

The client remains completely unaware of how the underlying SDK works.

---

## How to Identify This Pattern

You are likely looking at an Adapter Pattern if you notice:

- A wrapper class translating one interface into another.
- Third-party or legacy libraries being integrated without modification.
- The client interacting with a common interface while different implementations perform different underlying operations.
- Existing classes cannot be modified, so an intermediate object is introduced.

---

## Advantages

- ✅ Allows incompatible interfaces to work together.
- ✅ Reduces coupling between business logic and third-party libraries.
- ✅ Makes new integrations easy without modifying existing code.
- ✅ Encourages adherence to the Open/Closed Principle.
- ✅ Improves maintainability and testability.

---

## Disadvantages

- ❌ Introduces additional classes.
- ❌ Adds one more level of indirection.
- ❌ Can increase complexity if adapters become excessively large.
- ❌ May hide provider-specific capabilities behind a common interface.

---

## When Should You Use It?

Use the Adapter Pattern when:

- Integrating third-party SDKs with incompatible interfaces.
- Working with legacy code that cannot be modified.
- Standardizing multiple implementations behind a common interface.
- Migrating from one external library to another.

---

## When Should You Avoid It?

Avoid the Adapter Pattern when:

- Both classes already expose compatible interfaces.
- You own both implementations and can modify them directly.
- The adapter performs significant business logic instead of simple translation.
- The additional abstraction provides little value.

---

## Common Interview Questions

### Basic

- What problem does the Adapter Pattern solve?
- Why is it called an Adapter?
- What is the difference between the Client, Adapter, and Adaptee?

### Intermediate

- How does Adapter differ from Facade?
- How does Adapter help satisfy the Open/Closed Principle?
- Where have you used the Adapter Pattern in production?

### Advanced

- Can multiple adapters implement the same interface?
- How would you implement an Adapter using composition instead of inheritance?
- How would you integrate multiple payment providers using the Adapter Pattern?

---

## Related Patterns

| Pattern | Difference |
|----------|------------|
| Facade | Facade simplifies a complex subsystem. Adapter translates one interface into another. |
| Proxy | Proxy controls access to an object while preserving the same interface. Adapter changes the interface. |
| Decorator | Decorator adds new behavior dynamically. Adapter only translates interfaces. |
| Bridge | Bridge separates abstraction from implementation. Adapter makes incompatible interfaces work together. |

---

## Key Takeaways

- The Adapter Pattern enables classes with incompatible interfaces to collaborate.
- It introduces a translation layer without modifying either the client or the existing implementation.
- The client continues using the same interface while adapters handle provider-specific implementations.
- It is commonly used for third-party SDK integration, legacy system migration, and payment gateway abstraction.
- Adapter emphasizes compatibility, not new functionality.