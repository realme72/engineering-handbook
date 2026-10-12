# Template Method Pattern

## Intent

I use the Template Method Pattern whenever multiple implementations follow the same business workflow but differ in only a few steps.

When I notice different classes implementing nearly identical workflows with only a small portion of the logic changing, it's usually a sign that the common algorithm should be defined once in a base class while allowing subclasses to customize only the steps that vary.

The primary goal of the Template Method Pattern is to eliminate duplication, enforce a consistent workflow, and make changes to the overall algorithm in one place.

**What does the pattern do?**

It defines the overall workflow once while allowing subclasses to customize specific steps of the algorithm.

**How does it organize classes?**

A base class owns the complete algorithm and invokes a sequence of methods. Some methods contain common behavior, while others are left abstract or overridable for subclasses to implement.

**What design problem does it solve?**

It prevents multiple implementations from duplicating the same workflow while still allowing specific steps to vary.

---

# Why Was This Pattern Introduced?

Imagine you're building a payment platform.

Every payment provider follows the same high-level workflow.

```text
Validate Request

↓

Authenticate Merchant

↓

Process Payment

↓

Generate Receipt

↓

Send Notification
```

Now suppose you support

- Stripe
- Razorpay
- PayPal

A naive implementation would be

```python
class StripePayment:

    def pay(self):

        validate()

        authenticate()

        process_stripe_payment()

        generate_receipt()

        send_notification()
```

Then

```python
class RazorpayPayment:

    def pay(self):

        validate()

        authenticate()

        process_razorpay_payment()

        generate_receipt()

        send_notification()
```

Then

```python
class PayPalPayment:

    def pay(self):

        validate()

        authenticate()

        process_paypal_payment()

        generate_receipt()

        send_notification()
```

Initially this seems acceptable.

However, notice that only one step changes.

```text
Process Payment
```

Every other step is duplicated.

Now imagine the business asks you to change how receipts are generated.

You now modify every payment implementation.

The real problem isn't code duplication.

The problem is that multiple classes own the same business workflow.

The observation behind the Template Method Pattern is simple.

> The workflow is stable.

> Only a few steps vary.

Instead of allowing every implementation to redefine the entire algorithm, define the workflow once and allow subclasses to customize only the varying steps.

---

# Real-World Analogy

Think about baking different types of cakes.

Every recipe follows roughly the same process.

```text
Prepare Ingredients

↓

Mix Ingredients

↓

Bake

↓

Decorate

↓

Serve
```

Chocolate Cake changes the ingredients.

Vanilla Cake changes the ingredients.

Red Velvet Cake changes the ingredients.

The overall recipe never changes.

Only one step differs.

---

# Example 1 (Payment Processing)

Every payment provider follows

```text
Validate

↓

Authenticate

↓

Process Payment

↓

Generate Receipt

↓

Notify Customer
```

Only

```text
Process Payment
```

changes.

Instead of rewriting the entire workflow, the base class owns the algorithm while subclasses implement only the payment-specific logic.

---

# Example 2 (ETL Pipeline)

Suppose you're importing data.

Every import follows

```text
Read File

↓

Parse Data

↓

Transform Data

↓

Store Data

↓

Generate Report
```

CSV

JSON

XML

only differ in

```text
Parse Data
```

Everything else remains identical.

Template Method allows the pipeline to remain consistent while parsing is customized by each implementation.

---

# Python Implementation

```python
from abc import ABC, abstractmethod


class PaymentProcessor(ABC):

    def process_payment(self):

        self.validate_request()

        self.authenticate()

        self.process()

        self.generate_receipt()

        self.send_notification()

    def validate_request(self):
        print("Validating Request")

    def authenticate(self):
        print("Authenticating Merchant")

    @abstractmethod
    def process(self):
        pass

    def generate_receipt(self):
        print("Generating Receipt")

    def send_notification(self):
        print("Sending Notification")


class StripePayment(PaymentProcessor):

    def process(self):
        print("Processing Payment using Stripe")


class RazorpayPayment(PaymentProcessor):

    def process(self):
        print("Processing Payment using Razorpay")


processor = StripePayment()

processor.process_payment()
```

Output

```text
Validating Request

Authenticating Merchant

Processing Payment using Stripe

Generating Receipt

Sending Notification
```

---

# Internal Workflow

```text
Client

↓

Template Method

↓

Validate

↓

Authenticate

↓

Subclass Implementation

↓

Receipt

↓

Notification
```

The base class owns the workflow.

The subclass owns only the customizable step.

---

# How to Identify This Pattern

You are likely looking at the Template Method Pattern if you notice:

- Multiple classes implementing nearly identical workflows.
- Only one or two steps changing between implementations.
- Copy-pasted business logic across subclasses.
- Changes to the workflow requiring modifications in several classes.

---

# Advantages

- ✅ Eliminates duplicated workflows.
- ✅ Enforces a consistent business process.
- ✅ Changes to the workflow occur in one place.
- ✅ Subclasses focus only on the behavior that differs.

---

# Disadvantages

- ❌ Relies on inheritance.
- ❌ Deep inheritance hierarchies can become difficult to maintain.
- ❌ Less flexible than composition-based solutions.

---

# When Should You Use It?

- Payment processing pipelines.
- ETL/Data import pipelines.
- Authentication workflows.
- Report generation systems.
- Document processing.

---

# When Should You Avoid It?

- Every implementation follows a completely different workflow.
- Steps need to change dynamically at runtime.
- Composition would provide better flexibility.

---

# Common Interview Questions

## Basic

- What problem does the Template Method Pattern solve?
- Why not duplicate the workflow?

## Intermediate

- How is Template Method different from Strategy?
- Why is inheritance used here?

## Advanced

- Design a payment processing pipeline using Template Method.
- Design a file import framework supporting CSV, JSON and XML.
- What are the drawbacks of relying heavily on Template Method?

---

# Interview Answer

> I use the Template Method Pattern whenever multiple implementations follow the same business workflow but differ in only a few steps. Rather than duplicating the entire algorithm across multiple classes, I define the workflow once in a base class and allow subclasses to customize only the parts that vary. This keeps the workflow consistent, removes duplication, and ensures future changes to the overall process are made in a single location. A payment processing pipeline and an ETL framework are two common production examples where this pattern fits naturally.

---

# Related Patterns

| Pattern | Difference |
|----------|------------|
| Strategy | Strategy allows the client to choose between different algorithms at runtime. Template Method fixes the algorithm and allows subclasses to customize only specific steps. |
| State | State changes behavior based on an object's lifecycle. Template Method defines a fixed workflow regardless of state. |
| Command | Command represents an operation as an object. Template Method defines the structure of an operation. |
| Factory Method | Factory Method delegates object creation. Template Method delegates selected algorithm steps. |

---

# Key Takeaways

- Template Method defines the workflow once and customizes only the varying steps.
- It is best suited when the algorithm remains stable but individual steps differ.
- It eliminates duplicated workflows across multiple implementations.
- Prefer Strategy when the entire algorithm varies. Prefer Template Method when only a few steps change.