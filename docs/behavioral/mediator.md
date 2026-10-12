# Mediator Pattern

## Intent

I use the Mediator Pattern whenever multiple components need to collaborate and I notice them becoming tightly coupled to one another.

If I see services or objects directly communicating with several other components, it's usually a sign that the coordination logic should be centralized. Instead of allowing every component to know about every other component, I introduce a mediator responsible for coordinating their interactions.

The primary goal of the Mediator Pattern is to reduce coupling by centralizing communication while allowing each component to focus only on its own responsibility.

### What does the pattern do?

It introduces a central coordinator that manages communication between multiple components.

### How does it organize classes?

- **Client** triggers an operation.
- **Mediator** coordinates the workflow.
- **Colleagues (Components)** perform individual responsibilities.
- Components never communicate directly with one another.

### What design problem does it solve?

It prevents components from becoming tightly coupled by moving collaboration logic into a dedicated coordinator.

---

# Why Was This Pattern Introduced?

Imagine you're building an e-commerce checkout service.

Initially, placing an order is simple.

```python
checkout()

↓

inventory.reserve()

↓

payment.charge()
```

Everything looks fine.

As the business grows, additional requirements are introduced.

- Generate Invoice
- Send Email
- Update Analytics
- Notify CRM
- Trigger Recommendation Engine
- Send Slack Notification
- Publish Kafka Event
- Award Loyalty Points

A naive implementation quickly becomes

```python
class CheckoutService:

    def place_order(self):

        inventory.reserve()

        payment.charge()

        invoice.generate()

        email.send()

        analytics.track()

        crm.notify()

        loyalty.add_points()

        kafka.publish()

        slack.notify()
```

Initially this works.

But over time the dependencies grow.

Now Payment needs Inventory.

Inventory needs Email.

Analytics needs CRM.

CRM needs Loyalty.

Eventually every component starts knowing about every other component.

```text
Inventory ───── Payment

│               │

│               │

Analytics ─── Email

│               │

CRM ─────── Invoice
```

The real problem isn't the number of method calls.

The problem is that **communication logic is scattered across multiple components**, making the system difficult to maintain and extend.

The observation behind the Mediator Pattern is:

> Components shouldn't coordinate with each other directly.

Instead,

they should delegate coordination to one dedicated object.

---

# Real-World Analogy

Think about Air Traffic Control.

Without a control tower,

every airplane would need to communicate directly with every other airplane.

```text
Plane A

↓

Plane B

↓

Plane C

↓

Plane D
```

This becomes chaotic.

Instead,

every aircraft communicates only with the control tower.

```text
Plane A

↓

Air Traffic Control

↓

Plane B
```

The tower coordinates:

- Landing
- Takeoff
- Runway allocation

The airplanes remain completely unaware of one another.

---

# Example 1 (Checkout Orchestrator)

A Checkout Service coordinates multiple independent services.

```text
Checkout Request

↓

Checkout Mediator

↓

Inventory Service

↓

Payment Service

↓

Invoice Service

↓

Email Service

↓

Analytics Service
```

Notice:

- Inventory doesn't know Email exists.
- Payment doesn't know Analytics exists.
- Invoice doesn't know Loyalty exists.

Every component performs one responsibility.

The mediator decides **when** each service should be called.

---

# Example 2 (Workflow Engine / Microservice Orchestration)

A much more realistic production example is a workflow engine such as **Temporal**, **Camunda**, or **Netflix Conductor**.

Imagine an order workflow.

```text
Create Order

↓

Reserve Inventory

↓

Charge Payment

↓

Generate Invoice

↓

Notify Customer

↓

Publish Analytics Event
```

Rather than every microservice calling another service directly,

a workflow engine orchestrates the entire process.

```text
Order Service

↓

Workflow Engine

↓

Inventory Service

↓

Payment Service

↓

Invoice Service

↓

Notification Service

↓

Analytics Service
```

Each service focuses only on its own responsibility.

The workflow engine coordinates:

- execution order
- retries
- compensation
- timeouts
- failure handling

This is conceptually very similar to the Mediator Pattern.

Although Temporal operates across distributed services rather than objects inside one process, the underlying design principle is the same:

> Centralize collaboration while keeping participants independent.

---

# Python Implementation

```python
from abc import ABC, abstractmethod


class Mediator(ABC):

    @abstractmethod
    def place_order(self):
        pass


class InventoryService:

    def reserve(self):
        print("Inventory Reserved")


class PaymentService:

    def charge(self):
        print("Payment Successful")


class InvoiceService:

    def generate(self):
        print("Invoice Generated")


class EmailService:

    def send(self):
        print("Confirmation Email Sent")


class CheckoutMediator(Mediator):

    def __init__(self):

        self.inventory = InventoryService()
        self.payment = PaymentService()
        self.invoice = InvoiceService()
        self.email = EmailService()

    def place_order(self):

        self.inventory.reserve()

        self.payment.charge()

        self.invoice.generate()

        self.email.send()


checkout = CheckoutMediator()

checkout.place_order()
```

Output

```text
Inventory Reserved

Payment Successful

Invoice Generated

Confirmation Email Sent
```

---

# Internal Workflow

```text
Client

↓

Mediator

↓

Inventory

↓

Payment

↓

Invoice

↓

Email

↓

Analytics
```

Responsibilities:

- Client starts the workflow.
- Mediator coordinates communication.
- Components perform only their own work.

---

# How to Identify This Pattern

You are likely looking at the Mediator Pattern if you notice:

- Components communicating with many other components.
- Communication logic duplicated across services.
- One workflow coordinating several independent modules.
- Components becoming tightly coupled.

---

# Advantages

- ✅ Reduces coupling between components.
- ✅ Centralizes workflow logic.
- ✅ Easier to add new participants.
- ✅ Components remain focused on one responsibility.
- ✅ Simplifies testing.

---

# Disadvantages

- ❌ The mediator can become very large if it coordinates too many responsibilities.
- ❌ Poor design can create a "God Object."
- ❌ Complex workflows may require workflow engines instead of simple mediators.

---

# When Should You Use It?

- Checkout workflows.
- Order processing.
- Chat rooms.
- Air Traffic Control.
- Workflow orchestration.
- UI component coordination.

---

# When Should You Avoid It?

- Components rarely communicate.
- Communication is extremely simple.
- The mediator would become excessively complex.

---

# Common Interview Questions

## Basic

- What problem does the Mediator Pattern solve?
- Why is Air Traffic Control a good example?

## Intermediate

- How is Mediator different from Facade?
- How does Mediator reduce coupling?

## Advanced

- Design an e-commerce checkout using the Mediator Pattern.
- Would you use Mediator in a microservice architecture?
- When would you replace a Mediator with a workflow engine like Temporal?

---

# Interview Answer

> I use the Mediator Pattern whenever multiple components need to collaborate and I notice them becoming tightly coupled through direct communication. Instead of allowing every component to know about every other component, I introduce a mediator that coordinates their interactions. Each component remains responsible for only its own business logic while the mediator manages the workflow. A checkout orchestration service or a workflow engine coordinating inventory, payment, invoicing, and notifications are practical production examples of this idea.

---

# Related Patterns

| Pattern | Difference |
|----------|------------|
| Facade | Facade simplifies access to a subsystem. Mediator coordinates communication between peer components. |
| Observer | Observer broadcasts events to many subscribers. Mediator routes communication between specific components. |
| Chain of Responsibility | Passes a request through a pipeline of handlers. Mediator coordinates interactions among multiple components. |
| Command | Command represents an operation as an object. Mediator coordinates when and how multiple operations are invoked. |

---

# Key Takeaways

- Centralize communication, not business logic.
- Components should collaborate through a mediator rather than directly.
- The mediator owns the workflow.
- Checkout orchestration and workflow engines are excellent production examples.
- Temporal, Camunda, and Netflix Conductor apply the same design principle at a distributed systems level.
