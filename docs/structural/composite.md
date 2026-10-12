# Composite Pattern

## Intent

The Composite Pattern allows individual objects and groups of objects to be treated uniformly by organizing them into a tree-like hierarchy using a common interface.

Instead of distinguishing between a single object and a collection of objects, the client interacts with both in exactly the same way. This enables recursive structures while keeping client code simple and independent of the hierarchy.

### What does the pattern do?

It allows individual objects and compositions of objects to expose the same interface so that they can be treated uniformly.

### How does it work?

Each object implements a common interface. Composite objects maintain a collection of child objects, each of which also implements the same interface. Operations performed on a composite are delegated recursively to its children.

### What structural problem does it solve?

It eliminates the need for clients to distinguish between individual objects and groups of objects, making recursive hierarchical structures easier to model and traverse.

---

## Why Was This Pattern Introduced?

Consider a Reddit-like comment system.

Every post contains comments.

Each comment can have replies.

Each reply can have more replies.

A naive implementation might create separate classes for each level.

```text
Comment

↓

Reply

↓

ReplyToReply

↓

ReplyToReplyToReply
```

This quickly becomes impossible to maintain.

Another approach is writing conditional logic everywhere.

```python
if isinstance(node, Comment):
    ...

elif isinstance(node, Reply):
    ...

elif isinstance(node, ReplyToReply):
    ...
```

As the hierarchy grows, every operation becomes filled with type checks.

The Composite Pattern solves this by recognizing that every reply is fundamentally another comment.

Instead of multiple classes, we create a single `Comment` abstraction.

Each comment simply contains more comments.

```text
Comment

├── Comment

│      └── Comment

│              └── Comment

└── Comment
```

The client never needs to know whether it's dealing with a single comment or an entire comment tree.

---

## Real-World Analogy

Imagine a company.

An employee may be an individual contributor.

A manager is also an employee.

The only difference is that a manager manages other employees.

```text
CEO

├── Engineering Manager

│      ├── Software Engineer

│      └── Software Engineer

└── HR Manager

       └── Recruiter
```

Every node is still an employee.

Whether it's an individual contributor or an entire department, the organization can interact with both through the same abstraction.

---

## Software Engineering Example

One of the best production examples is a Reddit comment thread.

```text
How do I learn Python?

├── Start with the basics.

│      └── CS50 is a great course.

│              └── I completely agree.

└── Read Automate the Boring Stuff.
```

Every reply is itself another comment.

Instead of creating separate classes for comments and replies, both are represented using the same `Comment` class.

Operations such as

- Display
- Delete
- Count Replies
- Add Like

can be executed recursively without caring whether the node is a root comment or a nested reply.

Other production examples include:

- File Systems
- HTML DOM Tree
- React Component Tree
- Company Hierarchy
- Product Categories
- Organization Charts
- Menu/Submenu Systems

---

## Python Implementation

```python
from abc import ABC, abstractmethod


class CommentComponent(ABC):

    @abstractmethod
    def display(self, level=0):
        pass


class Comment(CommentComponent):

    def __init__(self, text):
        self.text = text
        self.replies = []

    def add_reply(self, reply):
        self.replies.append(reply)

    def display(self, level=0):

        print("    " * level + self.text)

        for reply in self.replies:
            reply.display(level + 1)


root = Comment("How do I learn Python?")

reply1 = Comment("Start with the basics.")

reply2 = Comment("CS50 is a great course.")

reply3 = Comment("I completely agree.")

reply4 = Comment("Read Automate the Boring Stuff.")


root.add_reply(reply1)
root.add_reply(reply4)

reply1.add_reply(reply2)

reply2.add_reply(reply3)


root.display()
```

**Output**

```text
How do I learn Python?
    Start with the basics.
        CS50 is a great course.
            I completely agree.
    Read Automate the Boring Stuff.
```

---

## Internal Workflow

When the client executes

```python
root.display()
```

the following sequence occurs.

```text
Client

        │

        ▼

Root Comment

        │

        ▼

Display Root

        │

        ▼

Iterate Replies

        │

        ▼

Reply.display()

        │

        ▼

Repeat recursively
```

Every comment behaves exactly the same way.

The client never checks whether a node is

- Root Comment
- Reply
- Reply to Reply

because every node exposes the same interface.

---

## How to Identify This Pattern

You are likely looking at a Composite Pattern if you notice:

- Recursive tree structures.
- Objects containing other objects of the same abstraction.
- A common interface shared by both leaf and parent nodes.
- Recursive traversal instead of conditional logic.

---

## Advantages

- ✅ Treats individual objects and groups uniformly.
- ✅ Simplifies recursive operations.
- ✅ Eliminates repeated type checking.
- ✅ Makes hierarchical structures easy to extend.
- ✅ Follows the Open/Closed Principle.

---

## Disadvantages

- ❌ Can make simple hierarchies appear more complex.
- ❌ Recursive operations may become expensive for very deep trees.
- ❌ Child management logic increases implementation complexity.

---

## When Should You Use It?

Use the Composite Pattern when:

- The domain naturally forms a tree structure.
- Individual objects and collections should be treated the same.
- Recursive traversal is common.
- Client code should remain independent of hierarchy depth.

---

## When Should You Avoid It?

Avoid the Composite Pattern when:

- The hierarchy is flat.
- Parent-child relationships do not exist.
- Recursive traversal provides no benefit.
- Simpler object relationships are sufficient.

---

## Common Interview Questions

### Basic

- What problem does the Composite Pattern solve?
- Why do both leaf and composite objects implement the same interface?
- Give a real-world example of Composite.

### Intermediate

- Why is a file system a Composite Pattern?
- How does Composite eliminate conditional logic?
- How does recursion simplify Composite implementations?

### Advanced

- Design a comment system using the Composite Pattern.
- How would you model an organization's hierarchy?
- Explain how React's component tree resembles the Composite Pattern.
- How would you implement recursive delete or search using Composite?

---

## Related Patterns

| Pattern | Difference |
|----------|------------|
| Decorator | Decorator wraps a single object to add behavior. Composite organizes objects into recursive tree structures. |
| Facade | Facade simplifies access to multiple subsystems. Composite models hierarchical object structures. |
| Bridge | Bridge separates abstraction from implementation. Composite represents parent-child hierarchies. |
| Flyweight | Flyweight shares object state to reduce memory usage. Composite organizes objects into trees. |

---

## Key Takeaways

- The Composite Pattern models tree-like structures using a common interface.
- Individual objects and groups of objects are treated uniformly.
- Recursive operations become simple because every node behaves the same way.
- File systems, Reddit comments, React component trees, and organization hierarchies are excellent real-world examples.
- The primary motivation is to eliminate special-case handling for leaf and composite objects.