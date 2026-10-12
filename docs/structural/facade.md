# Facade Pattern

## Intent

The Facade Pattern provides a simplified interface to a complex subsystem by hiding the interactions between multiple classes behind a single entry point.

Instead of allowing clients to communicate directly with every subsystem, the facade coordinates all the necessary operations internally. This reduces coupling and makes the system easier to use and maintain.

### What does the pattern do?

It introduces a single object that exposes a simplified interface while internally coordinating multiple subsystem objects.

### How does it work?

The client communicates only with the facade. The facade delegates work to the appropriate subsystem classes in the required sequence and returns the final result to the client.

### What structural problem does it solve?

It hides the complexity of a subsystem and prevents clients from depending on multiple classes directly. This centralizes orchestration logic and reduces coupling between clients and subsystem components.

---

## Why Was This Pattern Introduced?

Consider an e-commerce application where placing an order involves several independent services.

- Inventory Service
- Discount Engine
- Validation Service
- Payment Service
- Invoice Service
- Notification Service

Without a facade, every client must know the entire workflow.

```python
inventory_service.hold_inventory(request)

discount_service.apply_discount(request)

validation_service.validate(request)

payment_service.process_payment(request)

invoice_service.generate_invoice(request)

notification_service.send_email(request)
```

Now imagine multiple APIs performing the same workflow.

- Create Order
- Recreate Order
- Clone Order
- Retry Order

Each client duplicates the orchestration logic.

As the business evolves, the workflow also changes.

Suppose Fraud Detection is introduced before payment.

```text
Validation

↓

Fraud Detection

↓

Payment
```

Now every client needs to be updated.

This makes the code difficult to maintain and violates the Don't Repeat Yourself (DRY) principle.

The Facade Pattern solves this by introducing a single class responsible for orchestrating the workflow.

Clients simply invoke one method while the facade coordinates all subsystem interactions internally.

---

## Real-World Analogy

Imagine booking a vacation through a travel agency.

Without the agency, you must contact:

- Airline
- Hotel
- Taxi Service
- Tourist Guide
- Travel Insurance

individually.

With a travel agency, you simply say:

> "Book my vacation."

The travel agency coordinates everything behind the scenes.

You interact with only one interface while the agency communicates with multiple independent services.

The travel agency is the facade.

---

## Software Engineering Example

One of the best production examples is an Order Service.

Instead of every controller coordinating multiple services,

```python
inventory.reserve()

discount.apply()

validation.validate()

payment.process()

invoice.generate()

notification.send()
```

the controller simply calls

```python
order_facade.place_order(request)
```

Internally,

```text
OrderFacade

        │

        ├────────► Inventory Service

        ├────────► Discount Service

        ├────────► Validation Service

        ├────────► Payment Service

        ├────────► Invoice Service

        └────────► Notification Service
```

The controller knows nothing about the internal workflow.

Other production examples include:

- Checkout Service
- User Registration Service
- Payment Processing Service
- AWS SDK
- Database ORM
- Cloud SDKs

---

## Python Implementation

```python
class InventoryService:

    def reserve(self):
        print("Inventory Reserved")


class PaymentService:

    def process(self):
        print("Payment Processed")


class NotificationService:

    def send(self):
        print("Email Sent")


class OrderFacade:

    def __init__(self):
        self.inventory = InventoryService()
        self.payment = PaymentService()
        self.notification = NotificationService()

    def place_order(self):

        self.inventory.reserve()

        self.payment.process()

        self.notification.send()

        print("Order Created Successfully")


order = OrderFacade()

order.place_order()
```

**Output**

```text
Inventory Reserved

Payment Processed

Email Sent

Order Created Successfully
```

---

## Internal Workflow

When the client executes

```python
order.place_order()
```

the following sequence occurs.

```text
Client

        │

        ▼

OrderFacade

        │

        ├────────► Inventory Service

        ├────────► Payment Service

        └────────► Notification Service

        │

        ▼

Response
```

The client never communicates directly with subsystem classes.

Instead,

1. The client invokes the facade.
2. The facade coordinates all required subsystem operations.
3. Each subsystem performs its own responsibility.
4. The facade returns the final response.

The client remains completely unaware of the underlying workflow.

---

## How to Identify This Pattern

You are likely looking at a Facade Pattern if you notice:

- One class orchestrating multiple subsystem classes.
- Clients interacting with only a single object.
- Complex workflows hidden behind one method.
- Controllers containing very little business logic.

---

## Advantages

- ✅ Simplifies complex subsystems.
- ✅ Reduces coupling between clients and subsystem classes.
- ✅ Centralizes orchestration logic.
- ✅ Improves maintainability.
- ✅ Makes subsystem changes transparent to clients.

---

## Disadvantages

- ❌ Facade can become a "God Class" if too many responsibilities are added.
- ❌ May hide useful subsystem functionality from advanced clients.
- ❌ Adds another abstraction layer.

---

## When Should You Use It?

Use the Facade Pattern when:

- Multiple subsystem classes participate in a common workflow.
- Clients should not know subsystem details.
- Complex workflows need to be reused.
- You want to simplify an existing API.

---

## When Should You Avoid It?

Avoid the Facade Pattern when:

- The subsystem is already simple.
- Clients genuinely require direct access to subsystem functionality.
- The facade becomes responsible for unrelated business logic.

---

## Common Interview Questions

### Basic

- What problem does the Facade Pattern solve?
- How is Facade different from Adapter?
- Why is it called a Facade?

### Intermediate

- How is Facade different from a Service class?
- Does the Facade own the subsystem objects?
- Can subsystem classes still be accessed directly?

### Advanced

- How is Facade different from Mediator?
- How would you design an Order Processing Facade?
- Have you used the Facade Pattern in production?

---

## Related Patterns

| Pattern | Difference |
|----------|------------|
| Adapter | Adapter changes an interface. Facade simplifies a subsystem without changing interfaces. |
| Decorator | Decorator adds behavior to an object. Facade simplifies interaction with multiple objects. |
| Proxy | Proxy controls access to an object. Facade hides subsystem complexity. |
| Mediator | Mediator manages communication between peer objects. Facade provides a simplified interface to a subsystem. |

---

## Key Takeaways

- The Facade Pattern provides a simple interface to a complex subsystem.
- Clients communicate only with the facade instead of multiple subsystem classes.
- It centralizes orchestration logic and reduces coupling.
- Facade is commonly used in order processing, checkout flows, cloud SDKs, and service orchestration.
- A class doesn't need to be named "Facade" to implement the Facade Pattern. Many production classes like `OrderService`, `CheckoutService`, or `DocumentService` naturally act as facades by coordinating multiple services behind a single method.