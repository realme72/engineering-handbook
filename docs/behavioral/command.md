# Command Pattern

## Intent

The Command Pattern treats a **business operation as a first-class object** rather than executing it immediately.

Instead of directly invoking business logic, the client creates a command representing the work to be performed. Once an operation becomes an object, it carries its own data and lifecycle, making it possible to queue, retry, schedule, persist, audit, replay, or undo independently of the component that requested it.

Unlike a normal method call, a command can exist before, during, and after execution.

### What does the pattern do?

It represents an operation as an object so the operation itself can be managed.

### How does it organize classes?

- **Client** creates the command.
- **Command** represents the work.
- **Invoker** decides when to execute it.
- **Receiver** knows how to perform the actual work.

### What design problem does it solve?

It decouples the requester of an operation from its execution, allowing commands to be executed immediately, later, repeatedly, or on another machine.

---

# Why Was This Pattern Introduced?

Imagine you're building **Google Docs**.

Initially, editing is straightforward.

```python
editor.insert("Hello")
editor.delete(6)
editor.bold()
```

Everything works.

Then Product asks for:

- Undo
- Redo
- Keyboard Shortcuts
- Macro Recording
- Action History
- Replay User Actions

Now ask yourself:

After this executes,

```python
editor.delete(6)
```

where is the information required to undo it?

The method has already returned.

The application no longer knows:

- Which text was deleted?
- From what position?
- How should it be restored?

A simple method call is no longer enough.

The operation itself needs to become an object.

Instead of executing

```python
editor.delete(6)
```

we create

```text
DeleteCommand
```

The command stores:

- Receiver (Editor)
- Deleted Position
- Deleted Text

Now it can execute and undo itself.

This is the motivation behind the Command Pattern.

---

# Real-World Analogy

Think about ordering food in a restaurant.

You don't walk into the kitchen and cook your own meal.

Instead:

Customer

↓

Waiter writes an order slip

↓

Kitchen prepares food

The order slip can be:

- Stored
- Cancelled
- Delayed
- Repeated
- Tracked

The order slip is the **Command**.

---

# Example 1 (Google Docs)

Every user action becomes a command.

```text
Undo Stack

↓

InsertCommand

↓

DeleteCommand

↓

BoldCommand

↓

ItalicCommand
```

When the user clicks Undo,

```python
command = undo_stack.pop()
command.undo()
```

Redo simply executes the stored command again.

Because every action is represented as an object, the editor doesn't care whether it is deleting text, making text bold, or inserting an image.

---

# Example 2 (Production Background Job Scheduler)

Suppose you're building an e-commerce platform.

After an order is placed,

an email must be sent.

A naive implementation would do:

```python
email_service.send(order)
```

Problems:

- Email provider is slow.
- Email service is temporarily unavailable.
- Request latency increases.
- Retry logic pollutes the API layer.

Instead,

represent the work itself.

```text
SendEmailCommand(order_id)
```

Flow

```text
API

↓

Create SendEmailCommand

↓

RabbitMQ / SQS

↓

Background Worker

↓

command.execute()
```

Now the same command can be

- queued
- delayed
- retried
- audited
- persisted
- moved to a Dead Letter Queue
- replayed after recovery

without changing the API.

This is exactly why background job systems naturally align with the Command Pattern.

---

# Python Implementation

```python
from abc import ABC, abstractmethod


class Command(ABC):

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def undo(self):
        pass


class Editor:

    def __init__(self):
        self.text = "Hello World"

    def delete(self, position):
        deleted = self.text[position:]
        self.text = self.text[:position]
        return deleted

    def insert(self, position, text):
        self.text = self.text[:position] + text + self.text[position:]


class DeleteCommand(Command):

    def __init__(self, editor, position):
        self.editor = editor
        self.position = position
        self.deleted_text = ""

    def execute(self):
        self.deleted_text = self.editor.delete(self.position)

    def undo(self):
        self.editor.insert(self.position, self.deleted_text)


class EditorInvoker:

    def __init__(self):
        self.history = []

    def execute(self, command):
        command.execute()
        self.history.append(command)

    def undo(self):
        if self.history:
            self.history.pop().undo()


editor = Editor()
invoker = EditorInvoker()

print(editor.text)

cmd = DeleteCommand(editor, 6)
invoker.execute(cmd)

print(editor.text)

invoker.undo()

print(editor.text)
```

Output

```text
Hello World
Hello
Hello World
```

---

# Internal Workflow

```text
Client

↓

Creates Command

↓

Invoker

↓

execute()

↓

Command

↓

Receiver

↓

Business Logic
```

Responsibilities

- Client decides **what** should happen.
- Invoker decides **when** it should happen.
- Receiver knows **how** to do it.

---

# How to Identify This Pattern

You are likely looking at the Command Pattern if you notice:

- Operations are queued for later execution.
- Undo / Redo support.
- Background job processing.
- Task scheduling.
- Audit history.
- Replayable operations.
- A common `execute()` interface.

---

# Advantages

- ✅ Decouples requester from executor.
- ✅ Makes Undo / Redo easy.
- ✅ Enables scheduling and asynchronous execution.
- ✅ Supports retries, logging and auditing.
- ✅ New commands can be added without changing existing code.

---

# Disadvantages

- ❌ Introduces additional classes.
- ❌ Simple operations may become over-engineered.
- ❌ Undo often requires storing extra state.

---

# When Should You Use It?

- Undo / Redo systems.
- Background workers.
- Job schedulers.
- Task queues.
- Macro recording.
- Audit logging.

---

# When Should You Avoid It?

- Very small CRUD applications.
- Simple synchronous method calls with no future lifecycle.

---

# Common Interview Questions

## Basic

- What problem does the Command Pattern solve?
- Why represent work as an object?

## Intermediate

- How does it support Undo / Redo?
- How does it reduce coupling?

## Advanced

- Design Google Docs Undo/Redo using Command.
- Design a background job scheduler using Command.
- How would you retry failed commands?
- How would you persist commands for replay after a crash?

---

# Interview Answer

> I think of the Command Pattern as treating a business operation as a first-class object rather than an immediate method call. Once an operation becomes an object, it can carry its own data and lifecycle, allowing the infrastructure to queue it, schedule it, retry it, audit it, persist it, replay it, or undo it without changing the component that requested it. Google Docs' undo/redo stack and background job schedulers such as Celery or RabbitMQ-backed workers are practical examples where this pattern naturally fits.

---

# Related Patterns

| Pattern | Difference |
|----------|------------|
| Strategy | Strategy chooses **how** an algorithm executes. Command represents **the operation itself** as an object. |
| Observer | Observer broadcasts events. Command encapsulates executable work. |
| Chain of Responsibility | Passes a request through handlers. Command encapsulates a single request. |
| Template Method | Uses inheritance to vary an algorithm. Command encapsulates executable operations. |

---

# Key Takeaways

- Treat work as an object, not just a method call.
- Commands have their own lifecycle.
- Commands can be queued, retried, scheduled, audited, replayed, persisted, and undone.
- Google Docs and background job schedulers are classic production use cases.
