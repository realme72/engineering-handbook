# Memento Pattern

## Intent

I use the Memento Pattern whenever an object needs to restore one of its previous states without exposing or violating its internal representation.

If I notice external components trying to manage an object's internal state, or I need features like Undo/Redo, rollback, checkpoints, or version history, it's usually a sign that the object itself should be responsible for creating and restoring snapshots of its own state.

Instead of allowing other objects to directly inspect or modify its internal data, the object creates an immutable snapshot (Memento) that can later be used to restore a previous version of itself.

The primary goal of the Memento Pattern is to preserve encapsulation while allowing an object to save and restore its previous states.

### What does the pattern do?

It allows an object to capture its current state as a snapshot and restore itself from that snapshot later without exposing its internal implementation.

### How does it organize classes?

The pattern consists of three participants:

- **Originator** – The object whose state needs to be saved and restored.
- **Memento** – Stores a snapshot of the Originator's state.
- **Caretaker** – Maintains the history of snapshots without knowing their contents.

### What design problem does it solve?

It allows an object to maintain a history of its own state while keeping its internal representation hidden from the rest of the system.

---

# Why Was This Pattern Introduced?

Imagine you're building **Google Docs**.

Initially, editing is straightforward.

```python
editor.text = "Hello"

editor.text = "Hello World"

editor.text = "Hello World!!!"
```

Everything works perfectly.

Then Product asks for:

- Undo
- Redo
- Version History
- Auto Save
- Restore Previous Version

Now ask yourself.

After executing

```python
editor.text = "Hello World!!!"
```

where is the previous value?

```
Hello World
```

It's gone.

The application has permanently overwritten it.

---

## First Naive Solution

Someone introduces a variable.

```python
previous_text = editor.text

editor.text = "Hello World!!!"
```

Undo works exactly once.

Then the user edits again.

```python
previous_text = "Hello World!!!"
```

The older history has disappeared.

---

## Second Naive Solution

Store every version.

```python
history = []

history.append(editor.text)
```

Every edit saves the current document.

Undo becomes

```python
editor.text = history.pop()
```

This seems much better.

---

## The Real Problem

Who owns this history?

Suppose someone writes

```python
history[3] = "Corrupted Data"
```

or

```python
history.clear()
```

Now Undo no longer works correctly.

The editor's internal state is being manipulated by external code.

This violates encapsulation.

The document should be the only object that understands how its state is represented.

---

## The Observation

Instead of exposing the editor's internal state,

the editor should expose two operations.

```python
save()

restore()
```

The editor itself decides:

- What information should be saved.
- How that information is stored.
- How the state should be restored.

Nobody else knows the document's internal structure.

That observation leads to the Memento Pattern.

---

# Real-World Analogy

Think about a video game.

You're playing GTA or Assassin's Creed.

When you reach a checkpoint,

the game creates a save file.

Later,

you die.

The game restores the checkpoint.

Notice something important.

The player never knows:

- How the save file is structured.
- Which variables are stored.
- How health, inventory, and missions are restored.

Only the game understands its save file.

The save file is the Memento.

---

# Example 1 (Google Docs Undo / Redo)

Google Docs maintains a history of document snapshots.

```
Document

↓

Snapshot 1

↓

Edit

↓

Snapshot 2

↓

Edit

↓

Snapshot 3

↓

Edit
```

When the user clicks **Undo**,

Google Docs doesn't reverse the last operation.

Instead,

it restores the previous snapshot.

```
Undo

↓

Restore Snapshot 2
```

This allows users to travel backwards through document history.

Notice that the Undo system never modifies the document's internal data directly.

The document restores itself using one of its previously saved snapshots.

---

# Example 2 (Game Save Checkpoints & Database Rollback)

A game periodically creates checkpoints.

```
Checkpoint

↓

Player Progress

↓

Checkpoint

↓

Player Progress

↓

Checkpoint
```

If the player dies,

the game restores the most recent checkpoint.

The same idea exists in databases.

Before modifying important data,

the database keeps enough information to restore the previous state if a transaction fails.

```
Transaction Begins

↓

Snapshot

↓

Update Records

↓

Failure

↓

Rollback
```

Although databases use more sophisticated mechanisms internally (such as write-ahead logs), the underlying idea is very similar:

Restore a previously saved state without exposing internal storage details.

---

# Python Implementation

```python
class Memento:

    def __init__(self, state):
        self._state = state

    def get_state(self):
        return self._state


class Document:

    def __init__(self):
        self.text = ""

    def write(self, text):
        self.text += text

    def save(self):
        return Memento(self.text)

    def restore(self, memento):
        self.text = memento.get_state()


class History:

    def __init__(self):
        self.history = []

    def push(self, memento):
        self.history.append(memento)

    def pop(self):
        return self.history.pop()


document = Document()

history = History()

document.write("Hello")

history.push(document.save())

document.write(" World")

history.push(document.save())

document.write("!!!")

print(document.text)

document.restore(history.pop())

print(document.text)
```

Output

```text
Hello World!!!

Hello World
```

---

# Internal Workflow

The Memento Pattern consists of three participants.

```text
                Creates Snapshot
                       │
                       ▼
                 +-------------+
                 |  Memento    |
                 +-------------+
                        ▲
                        │
              Save      │     Restore
                        │
                        │
+------------+          │          +-------------+
| Document   |──────────┘          |   History   |
| (Originator)|<──────────────────>| (Caretaker) |
+------------+                     +-------------+
```

### Responsibilities

**Originator (Document)**

- Owns the actual business state.
- Creates snapshots of itself.
- Restores itself from a snapshot.

**Memento**

- Stores the snapshot.
- Does not contain business logic.
- Should ideally be immutable.

**Caretaker**

- Maintains snapshot history.
- Never modifies snapshot contents.
- Doesn't understand the internal structure of a snapshot.

Notice something important.

The Caretaker never accesses

```python
memento._state
```

It simply stores and retrieves snapshots.

This preserves encapsulation.

---

# How to Identify This Pattern

You are likely looking at the Memento Pattern if you notice:

- Undo / Redo functionality.
- Checkpoints or Save Game features.
- Rollback mechanisms.
- Version history.
- Objects creating snapshots of themselves.
- External components storing snapshots without understanding their contents.

---

# Advantages

- ✅ Preserves encapsulation by hiding internal state.
- ✅ Makes Undo / Redo straightforward.
- ✅ Supports checkpoints and version history.
- ✅ Originator remains responsible for its own state.
- ✅ Easy to restore previous versions.

---

# Disadvantages

- ❌ Saving large object graphs can consume significant memory.
- ❌ Frequent snapshots may impact performance.
- ❌ Snapshot history must often be managed or pruned.
- ❌ Deep copying complex objects can become expensive.

---

# When Should You Use It?

Use the Memento Pattern when:

- Undo / Redo functionality is required.
- Objects need checkpointing.
- Rollback support is required.
- Version history must be maintained.
- Object state should remain encapsulated.

Typical examples:

- Google Docs
- Microsoft Word
- VS Code
- IntelliJ IDEA
- Database rollback
- Game save checkpoints

---

# When Should You Avoid It?

Avoid the Memento Pattern when:

- Objects are extremely large.
- Snapshot creation is prohibitively expensive.
- State restoration is never required.
- Event sourcing or audit logging is a better fit.

---

# Common Interview Questions

## Basic

- What problem does the Memento Pattern solve?
- Why not simply expose object fields?
- What is the responsibility of the Caretaker?

---

## Intermediate

- Why should the Caretaker not modify snapshots?
- How does Memento preserve encapsulation?
- What are the memory implications of storing snapshots?

---

## Advanced

- How would you implement multiple Undo and Redo?
- How would you optimize memory usage for large objects?
- How is Memento different from Event Sourcing?
- Would you use deep copy or shallow copy?
- How would you implement version history for a collaborative editor?

---

# Interview Answer

> I use the Memento Pattern whenever an object needs to restore one of its previous states without exposing or violating its internal representation. Rather than allowing external components to manipulate the object's internal data directly, the object creates immutable snapshots of itself that can later be used to restore an earlier version. The Caretaker simply manages these snapshots without understanding their contents. I commonly think about this pattern when designing Undo/Redo systems, game save checkpoints, rollback mechanisms, and version history.

---

# Memento vs Command

This is one of the most common interview questions.

Although both patterns are associated with Undo functionality, they solve different problems.

| Pattern | Stores | Typical Use |
|----------|---------|-------------|
| **Command** | The operation to execute (or undo) | Undo/Redo, Job Queues, Scheduling |
| **Memento** | A snapshot of object state | Checkpoints, Rollback, Version History |

### Command

Command remembers **what happened**.

Example:

```python
DeleteCommand

↓

Position = 15

Deleted Text = "World"
```

Undo executes

```python
command.undo()
```

The command reverses its own operation.

---

### Memento

Memento remembers **what existed**.

Example:

```text
Document Snapshot

↓

Hello World
```

Undo simply restores

```python
document.restore(snapshot)
```

No knowledge of individual operations is required.

---

### Which one should you choose?

Use **Command** when individual operations can naturally reverse themselves.

Examples:

- Delete
- Insert
- Move
- Resize

Use **Memento** when restoring an entire object state is simpler than reversing every individual operation.

Examples:

- Document editors
- Game checkpoints
- Database rollback
- Configuration snapshots

In many real-world systems, both patterns are used together.

For example,

Google Docs can use:

- Command to represent editing operations.
- Memento to periodically create checkpoints.

This allows efficient Undo while avoiding replaying thousands of commands after long editing sessions.

---

# Related Patterns

| Pattern | Difference |
|----------|------------|
| Command | Command stores operations. Memento stores object state. |
| State | State changes object behavior. Memento restores previous object state. |
| Prototype | Prototype creates new objects by cloning. Memento captures snapshots of an existing object. |
| Visitor | Visitor performs operations on objects without modifying their classes. Memento focuses on preserving object state. |

---

# Key Takeaways

- Memento preserves encapsulation while allowing state restoration.
- The Originator is responsible for creating and restoring snapshots.
- The Caretaker manages snapshots but never understands their contents.
- Undo, rollback, checkpoints, and version history are classic applications.
- Command remembers **operations**; Memento remembers **state**.