# Observer Pattern

## Intent

The Observer Pattern is used when one part of the system needs to notify multiple independent components that something has happened, without knowing who those components are.

Instead of tightly coupling the publisher to every downstream operation, the publisher simply announces an event. Any interested component can subscribe to that event and react independently.

The primary goal of the Observer Pattern is to reduce coupling by separating an event from the actions performed in response to that event.

### What does the pattern do?

It allows one object to publish events while multiple independent objects subscribe and react to those events.

### How does it work?

The publisher maintains a list of subscribers. Whenever an event occurs, it notifies every registered subscriber by invoking a common method. The publisher doesn't know what each subscriber does; it only knows that they can handle the event.

### What design problem does it solve?

It prevents a class from becoming tightly coupled to every component that needs to react to an event, making the system easier to extend without modifying existing business logic.

---

## Why Was This Pattern Introduced?

Suppose you're building an e-commerce application.

When an order is placed, several independent actions need to occur.

- Reserve inventory
- Send confirmation email
- Generate invoice
- Update analytics
- Add loyalty points

A naive implementation might look like this.

```python
class OrderService:

    def place_order(self):

        inventory_service.reserve_items()

        email_service.send_confirmation()

        invoice_service.generate()

        analytics_service.track_order()

        loyalty_service.add_reward_points()
```

Initially, this looks reasonable.

However, as the application evolves, more business requirements are introduced.

- Notify the CRM system
- Send a Slack notification
- Trigger fraud detection
- Publish an event to Kafka
- Update recommendation models

Every new requirement forces us to modify `OrderService`.

The service gradually becomes responsible for much more than simply placing an order.

This violates the Single Responsibility Principle and the Open/Closed Principle.

The Observer Pattern solves this by changing the conversation.

Instead of asking:

> Which services should I call?

the publisher asks:

> What event just happened?

The publisher simply announces:

```text
OrderPlaced
```

Every interested component independently reacts to that event.

---

## Real-World Analogy

Imagine a newspaper subscription.

The newspaper company prints today's newspaper.

Subscribers decide whether they want to receive it.

The newspaper company doesn't know:

- Who reads sports.
- Who reads business news.
- Who immediately throws it away.

Its only responsibility is publishing today's newspaper.

Similarly, an event publisher announces an event without knowing what each subscriber intends to do with it.

---

## Software Engineering Example

An Order Service is one of the best production examples.

Instead of

```text
Order Service

↓

Inventory

↓

Email

↓

Invoice

↓

Analytics

↓

Loyalty
```

we publish an event.

```text
Order Service

↓

OrderPlaced Event

↓

Inventory Service

↓

Email Service

↓

Invoice Service

↓

Analytics Service

↓

Loyalty Service
```

Now adding another consumer is straightforward.

For example,

```text
OrderPlaced

↓

Fraud Detection Service
```

No changes are required inside `OrderService`.

Other production examples include:

- User Registration Events
- Payment Successful Events
- CI/CD Pipeline Notifications
- GitHub Webhooks
- Stock Price Alerts
- Event-driven Microservices

---

## Python Implementation

```python
from abc import ABC, abstractmethod


class Observer(ABC):

    @abstractmethod
    def update(self, event):
        pass


class InventoryService(Observer):

    def update(self, event):
        print("Inventory Reserved")


class EmailService(Observer):

    def update(self, event):
        print("Confirmation Email Sent")


class AnalyticsService(Observer):

    def update(self, event):
        print("Analytics Updated")


class OrderService:

    def __init__(self):
        self.observers = []

    def subscribe(self, observer):
        self.observers.append(observer)

    def notify(self, event):

        for observer in self.observers:
            observer.update(event)

    def place_order(self):

        print("Order Created")

        self.notify("OrderPlaced")


order_service = OrderService()

order_service.subscribe(InventoryService())
order_service.subscribe(EmailService())
order_service.subscribe(AnalyticsService())

order_service.place_order()
```

**Output**

```text
Order Created

Inventory Reserved

Confirmation Email Sent

Analytics Updated
```

---

## Internal Workflow

When the client executes

```python
order_service.place_order()
```

the following sequence occurs.

```text
Client

        │

        ▼

OrderService

        │

Publishes

        ▼

OrderPlaced Event

        │

────────┼────────────────────────────

│        │                      │

▼        ▼                      ▼

Inventory Email            Analytics
Service    Service          Service

        │

        ▼

Independent Processing
```

Notice that the `OrderService` never directly invokes any downstream service.

Its only responsibility is publishing the event.

Subscribers decide independently how to react.

---

## How to Identify This Pattern

You are likely looking at an Observer Pattern if you notice:

- One event triggers multiple independent actions.
- New listeners can be added without modifying the publisher.
- The publisher doesn't know who consumes the event.
- Components communicate through notifications rather than direct method calls.

---

## Advantages

- ✅ Reduces coupling between components.
- ✅ Follows the Open/Closed Principle.
- ✅ Makes new subscribers easy to introduce.
- ✅ Encourages event-driven architecture.
- ✅ Keeps responsibilities well separated.

---

## Disadvantages

- ❌ Debugging becomes more difficult because execution is indirect.
- ❌ Event ordering may become important.
- ❌ Too many observers can impact performance.
- ❌ Hidden dependencies may emerge if events are poorly documented.

---

## When Should You Use It?

Use the Observer Pattern when:

- One event triggers multiple independent actions.
- Publishers shouldn't know about downstream consumers.
- New reactions should be added without modifying existing code.
- Loose coupling is preferred over direct service-to-service communication.

---

## When Should You Avoid It?

Avoid the Observer Pattern when:

- Only one consumer exists.
- The publisher must receive immediate responses from consumers.
- Operations require strict execution order or transactional consistency.

---

## Common Interview Questions

### Basic

- What problem does the Observer Pattern solve?
- Why is it better than directly calling dependent services?
- What is the difference between a publisher and a subscriber?

### Intermediate

- How does the Observer Pattern reduce coupling?
- How would you unsubscribe an observer?
- Can multiple observers react to the same event?

### Advanced

- How is Kafka related to the Observer Pattern?
- How would you implement asynchronous observers?
- How would you guarantee delivery if a subscriber fails?
- How would you prevent slow observers from blocking the publisher?

---

## Interview Answer

### How would you explain the Observer Pattern in an interview?

> The Observer Pattern is useful when one part of the system needs to notify multiple independent components that an event has occurred without being tightly coupled to those components. Rather than directly invoking every downstream dependency, the publisher simply announces an event, and any interested subscriber can react independently.
>
> I usually think about the Observer Pattern whenever a service starts growing because it repeatedly calls unrelated downstream services. Instead of embedding those calls inside the publisher, I publish an event and allow independent subscribers to handle their own responsibilities. This keeps the publisher focused on its core responsibility while making the system easier to extend as new business requirements emerge.
>
> A common production example is an Order Service. After an order is placed, inventory reservation, email notifications, invoice generation, analytics tracking, and loyalty point updates all happen independently. Rather than hardcoding these operations inside the Order Service, the service publishes an `OrderPlaced` event, allowing each subscriber to process the event without modifying the publisher.

---

## Related Patterns

| Pattern | Difference |
|----------|------------|
| Strategy | Strategy selects one algorithm to execute. Observer notifies multiple independent subscribers about an event. |
| Command | Command encapsulates a request. Observer broadcasts an event to interested subscribers. |
| Mediator | Mediator centralizes communication between objects. Observer allows one-to-many event notifications. |
| Chain of Responsibility | Chain of Responsibility passes a request through handlers until one handles it. Observer notifies all subscribed observers. |

---

## Key Takeaways

- The Observer Pattern separates an event from the actions performed in response to that event.
- Publishers announce events without knowing who consumes them.
- Subscribers independently react to events through a common interface.
- The pattern reduces coupling and makes systems easier to extend.
- Order processing, user registration, webhooks, CI/CD pipelines, and event-driven microservices are excellent production examples.