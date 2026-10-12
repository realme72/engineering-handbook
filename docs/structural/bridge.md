# Bridge Pattern

## Intent

The Bridge Pattern separates an abstraction from its implementation so that both can evolve independently.

Instead of combining multiple dimensions of variation using inheritance, the pattern uses composition to connect an abstraction with its implementation. This prevents an explosion of subclasses and makes both hierarchies easier to extend and maintain.

### What does the pattern do?

It decouples an abstraction from its implementation by replacing inheritance with composition.

### How does it work?

The abstraction maintains a reference to an implementation object rather than inheriting from it. Both hierarchies evolve independently while collaborating through composition.

### What structural problem does it solve?

It prevents class explosion when a class has multiple independently changing dimensions by separating those dimensions into independent hierarchies.

---

## Why Was This Pattern Introduced?

Consider a notification system.

Initially, the application supports two notification channels.

- Email
- SMS

A straightforward implementation might create

```text
EmailNotification

SMSNotification
```

Everything works fine.

Later, the business introduces different notification types.

- Alert
- Reminder
- Marketing

A naive inheritance hierarchy quickly becomes

```text
AlertEmail

AlertSMS

ReminderEmail

ReminderSMS

MarketingEmail

MarketingSMS
```

Now suppose another notification channel is added.

- WhatsApp

The hierarchy grows again.

```text
AlertWhatsApp

ReminderWhatsApp

MarketingWhatsApp
```

As new notification types and delivery channels are introduced, the number of classes grows multiplicatively.

```text
Notification Types

×

Delivery Channels
```

This makes the system difficult to maintain and violates the Open/Closed Principle.

The Bridge Pattern solves this by separating the two independent dimensions.

Instead of inheritance,

```text
AlertEmail
```

becomes

```text
Alert

↓

EmailSender
```

The notification type and the delivery mechanism evolve independently.

---

## Real-World Analogy

Imagine a television.

A television can be manufactured by different companies.

- Sony
- Samsung
- LG

The television can also be controlled using different remote controls.

- Basic Remote
- Smart Remote
- Voice Remote

Instead of creating

```text
SonyBasicRemote

SonySmartRemote

SamsungBasicRemote

SamsungSmartRemote
```

the remote simply holds a reference to a television.

```text
Remote

↓

Television
```

Both remotes and televisions evolve independently.

---

## Software Engineering Example

A notification system is one of the best production examples.

Instead of creating

```text
AlertEmail

AlertSMS

ReminderEmail

ReminderSMS

MarketingEmail

MarketingSMS
```

we separate the responsibilities.

```text
Notification

↓

Sender
```

Notification hierarchy

```text
Alert

Reminder

Marketing
```

Sender hierarchy

```text
Email

SMS

WhatsApp

Push Notification
```

Now any notification type can work with any sender.

Examples:

```python
Alert(EmailSender())

Alert(SMSSender())

Reminder(WhatsAppSender())

Marketing(PushSender())
```

Adding a new sender or notification type no longer requires modifying existing classes.

Other production examples include:

- Database Repository → PostgreSQL / MySQL / MongoDB
- Payment Service → Stripe / Razorpay / PayPal
- UI Components → Windows / macOS / Linux
- Storage Service → S3 / GCS / Azure Blob Storage

---

## Python Implementation

```python
from abc import ABC, abstractmethod


class Sender(ABC):

    @abstractmethod
    def send(self, message):
        pass


class EmailSender(Sender):

    def send(self, message):
        print(f"Email: {message}")


class SMSSender(Sender):

    def send(self, message):
        print(f"SMS: {message}")


class Notification(ABC):

    def __init__(self, sender):
        self.sender = sender

    @abstractmethod
    def notify(self, message):
        pass


class Alert(Notification):

    def notify(self, message):
        print("Alert Notification")
        self.sender.send(message)


class Reminder(Notification):

    def notify(self, message):
        print("Reminder Notification")
        self.sender.send(message)


notification = Alert(EmailSender())

notification.notify("Server CPU usage exceeded 90%")
```

**Output**

```text
Alert Notification
Email: Server CPU usage exceeded 90%
```

---

## Internal Workflow

When the client executes

```python
notification.notify(message)
```

the following sequence occurs.

```text
Client

        │

        ▼

Alert

        │

Delegates

        ▼

EmailSender

        │

        ▼

Send Email
```

Notice that the notification knows **what** should happen.

The sender knows **how** it should happen.

Each class has a single responsibility.

---

## How to Identify This Pattern

You are likely looking at a Bridge Pattern if you notice:

- Two independent class hierarchies that change for different reasons.
- A rapidly growing inheritance hierarchy.
- Composition replacing inheritance.
- One object delegating work to another implementation object.

---

## Advantages

- ✅ Prevents class explosion.
- ✅ Encourages composition over inheritance.
- ✅ Allows abstraction and implementation to evolve independently.
- ✅ Improves maintainability.
- ✅ Follows the Open/Closed Principle.

---

## Disadvantages

- ❌ Introduces additional abstraction.
- ❌ Can be unnecessary for simple systems.
- ❌ Slightly increases design complexity.

---

## When Should You Use It?

Use the Bridge Pattern when:

- A class has multiple independent dimensions of variation.
- Inheritance is producing too many subclasses.
- Both abstraction and implementation should evolve independently.
- Composition provides a cleaner design than inheritance.

---

## When Should You Avoid It?

Avoid the Bridge Pattern when:

- There is only one implementation.
- The abstraction and implementation are tightly coupled.
- The additional abstraction provides little benefit.

---

## Common Interview Questions

### Basic

- What problem does the Bridge Pattern solve?
- Why is composition preferred over inheritance in Bridge?
- What are the Abstraction and Implementation hierarchies?

### Intermediate

- How is Bridge different from Adapter?
- How does Bridge prevent class explosion?
- Give a real-world example of the Bridge Pattern.

### Advanced

- Design a payment system using the Bridge Pattern.
- How would you model notification types and delivery channels?
- Explain how Bridge follows the Open/Closed Principle.
- When would you choose Bridge over Strategy?

---

## Related Patterns

| Pattern | Difference |
|----------|------------|
| Adapter | Adapter converts one interface into another. Bridge separates abstraction from implementation before either hierarchy grows. |
| Composite | Composite models recursive tree structures. Bridge separates independent dimensions of variation. |
| Strategy | Strategy changes an algorithm at runtime. Bridge separates two independent class hierarchies. |
| Decorator | Decorator dynamically adds behavior. Bridge organizes abstractions and implementations using composition. |

---

## Key Takeaways

- The Bridge Pattern separates abstraction from implementation using composition.
- Its primary goal is to prevent an explosion of subclasses.
- The abstraction decides **what** should happen, while the implementation decides **how** it happens.
- Two independent hierarchies can evolve without affecting one another.
- Notification systems, payment providers, repositories, cloud storage SDKs, and UI frameworks are common production examples.