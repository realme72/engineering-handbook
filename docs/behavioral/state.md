# State Pattern

## Intent

I start thinking about the State Pattern whenever an object's behavior changes based on where it is in its lifecycle.

When I see multiple methods repeatedly asking questions like "Is the order paid?", "Has it been shipped?", or "Is the subscription active?" before deciding what to do, I know the lifecycle rules are leaking into the business logic. Rather than continuing to add more conditional checks, I move the behavior for each lifecycle stage into its own state object. The object simply delegates the request to its current state, and the state decides whether the operation is valid and what the next state should be.

This keeps lifecycle rules isolated, reduces duplication, and makes it much easier to evolve the workflow as new states are introduced.

### What does the pattern do?

It allows an object's behavior to change automatically as its internal state changes.

### How does it organize classes?

- **Context** owns the current state.
- **State Interface** defines common operations.
- **Concrete States** implement behavior for a specific lifecycle stage.
- States can transition the Context into another state.

### What design problem does it solve?

It removes duplicated lifecycle checks (`if status == ...`) from business logic by letting each state own its own behavior and transitions.

---

# Why Was This Pattern Introduced?

Imagine you're building an Order Management System.

An order moves through this lifecycle.

```text
Created

↓

Paid

↓

Packed

↓

Shipped

↓

Delivered
```

A naive implementation usually starts like this.

```python
class Order:

    def ship(self):

        if self.status != "PAID":
            raise Exception("Only paid orders can be shipped")

        self.status = "SHIPPED"

    def cancel(self):

        if self.status == "DELIVERED":
            raise Exception("Delivered orders cannot be cancelled")

        self.status = "CANCELLED"
```

Initially, this looks fine.

Then Product introduces:

- Returned
- Refunded
- Lost in Transit
- Replacement Sent
- On Hold
- Exchange Requested

Soon every method contains lifecycle checks.

```python
if self.status == ...
```

Those rules become duplicated across the class.

The real problem isn't the `if` statements.

The problem is that **Order** is now responsible for both managing orders and understanding every lifecycle transition.

Those are different responsibilities.

The observation behind the State Pattern is:

> The current state already knows what operations are valid and where the object should transition next.

Instead of asking

```python
if order.status == "PAID":
```

we simply ask

```python
order.state.ship(order)
```

The state decides.

---

# Real-World Analogy

Think about an ATM.

Its behavior depends entirely on its current state.

```text
No Card

↓

Card Inserted

↓

PIN Verified

↓

Transaction

↓

Cash Dispensed
```

Calling

```text
Withdraw Cash
```

while the ATM is in **No Card** is invalid.

Instead of writing

```python
if state == "NO_CARD":
```

the `NoCardState` simply rejects the request.

Each state owns its own rules.

---

# Software Engineering Example 1 (Order Lifecycle)

Every order state becomes an object.

```text
Order

↓

CreatedState

↓

PaidState

↓

ShippedState

↓

DeliveredState
```

Instead of checking the order status before every operation,

the context delegates work.

```python
order.ship()
```

↓

```python
order.state.ship(order)
```

`PaidState` allows shipping.

`ShippedState` rejects it because the order has already shipped.

No duplicated conditional logic.

---

# Software Engineering Example 2 (Netflix Subscription)

A subscription moves through several states.

```text
Trial

↓

Active

↓

Paused

↓

Expired

↓

Cancelled
```

Instead of

```python
if subscription.status == "ACTIVE":
```

the subscription delegates

```python
subscription.play_movie()
```

↓

```python
subscription.state.play_movie(subscription)
```

Each state determines whether playback is allowed.

---

# Python Implementation

```python
from abc import ABC, abstractmethod


class State(ABC):

    @abstractmethod
    def ship(self, order):
        pass


class PaidState(State):

    def ship(self, order):
        print("Shipping Order")
        order.state = ShippedState()


class ShippedState(State):

    def ship(self, order):
        raise Exception("Order has already been shipped")


class Order:

    def __init__(self):
        self.state = PaidState()

    def ship(self):
        self.state.ship(self)


order = Order()

order.ship()

print(type(order.state).__name__)

order.ship()
```

Output

```text
Shipping Order
ShippedState
Exception: Order has already been shipped
```

---

# Internal Workflow

```text
Client

↓

Order Context

↓

Current State

↓

Execute State-specific Behavior

↓

Optional State Transition
```

Responsibilities:

- Context knows the current state.
- State knows what is valid.
- State decides the next state.

---

# How to Identify This Pattern

You are likely looking at the State Pattern if you notice:

- Objects move through a well-defined lifecycle.
- Behavior changes based on current state.
- Large `if-else` or `switch` statements checking status values.
- State transitions are becoming difficult to maintain.

---

# Advantages

- ✅ Eliminates duplicated lifecycle checks.
- ✅ Localizes state-specific behavior.
- ✅ Makes new states easier to introduce.
- ✅ Follows the Open/Closed Principle.

---

# Disadvantages

- ❌ More classes are introduced.
- ❌ Overkill for objects with only one or two states.
- ❌ State transitions must be designed carefully.

---

# When Should You Use It?

- Order management systems.
- Subscription lifecycle management.
- Workflow engines.
- ATM or vending machine software.
- Document approval workflows.

---

# When Should You Avoid It?

- Only a couple of simple states exist.
- State never affects behavior.
- Lifecycle is unlikely to grow.

---

# Common Interview Questions

## Basic

- What problem does the State Pattern solve?
- Why is it better than multiple `if-else` statements?

## Intermediate

- How is State different from Strategy?
- Who should own state transitions?

## Advanced

- Design an Order Lifecycle using the State Pattern.
- Design an ATM using the State Pattern.
- How would you persist and restore object state across application restarts?

---

# Interview Answer

> I use the State Pattern whenever an object's behavior changes as it moves through a lifecycle. Rather than scattering state checks throughout the codebase, each lifecycle stage becomes its own object responsible for defining valid behavior and transitioning to the next state. This keeps lifecycle rules localized, reduces conditional logic, and makes it easier to extend workflows as new states are introduced. A typical production example is an order moving from Paid to Shipped to Delivered, where each state controls what operations are valid.

---

# Related Patterns

| Pattern | Difference |
|----------|------------|
| Strategy | Strategy lets the client choose an algorithm. State changes behavior automatically as the object's lifecycle changes. |
| Command | Command represents work as an object. State represents lifecycle behavior. |
| Template Method | Template Method varies steps through inheritance. State varies behavior through composition. |
| Chain of Responsibility | Passes a request through handlers. State delegates to the current lifecycle state only. |

---

# Key Takeaways

- Model lifecycle stages as objects.
- Let the current state decide valid behavior.
- Remove scattered `if status == ...` checks.
- Lifecycle rules become easier to extend and maintain.
