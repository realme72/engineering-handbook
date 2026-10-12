# Chain of Responsibility Pattern

## Intent

I use the Chain of Responsibility Pattern whenever a request needs to pass through multiple independent processing steps, and I don't want the caller to know or manage the entire workflow.

If I notice a service repeatedly orchestrating authentication, authorization, validation, logging, rate limiting, and other checks in one place, it's usually a sign that the request processing pipeline should be decomposed into independent handlers. Each handler becomes responsible for one concern and decides whether the request should continue to the next handler.

The primary goal of the Chain of Responsibility Pattern is to build a flexible processing pipeline where handlers remain loosely coupled and can be added, removed, or reordered without changing the client.

## What does the pattern do?

It passes a request through a chain of handlers, where each handler performs one responsibility and decides whether to forward the request.

## Why Was This Pattern Introduced?

Imagine an API request passing through:

Authentication
→ Authorization
→ Rate Limiting
→ Validation
→ Business Logic

A naive implementation hardcodes every step inside one method. As more requirements like maintenance mode, IP whitelisting, logging, and feature flags are added, the orchestration method keeps growing.

Instead, each processing step becomes its own handler and only knows about the next handler.

## Example

HTTP middleware is one of the best production examples.

Incoming Request
→ Logging Middleware
→ Authentication Middleware
→ Authorization Middleware
→ Validation Middleware
→ Business Logic

If authentication fails, the chain stops immediately.

## Python Implementation

```python
from abc import ABC, abstractmethod

class Handler(ABC):

    def __init__(self):
        self.next = None

    def set_next(self, handler):
        self.next = handler
        return handler

    @abstractmethod
    def handle(self, request):
        pass


class AuthenticationHandler(Handler):

    def handle(self, request):
        if not request.get("authenticated"):
            print("Authentication Failed")
            return

        print("Authentication Passed")

        if self.next:
            self.next.handle(request)


class ValidationHandler(Handler):

    def handle(self, request):
        print("Validation Passed")

        if self.next:
            self.next.handle(request)


class BusinessHandler(Handler):

    def handle(self, request):
        print("Business Logic Executed")


auth = AuthenticationHandler()
validation = ValidationHandler()
business = BusinessHandler()

auth.set_next(validation).set_next(business)

auth.handle({"authenticated": True})
```

## Internal Workflow

Client
↓
Authentication Handler
↓
Validation Handler
↓
Business Handler

Each handler performs its own work and decides whether the request should continue.

## Advantages

- Single responsibility for each handler.
- Easy to add, remove, or reorder handlers.
- Reduces coupling.
- Excellent for middleware pipelines.

## Disadvantages

- Long chains can be difficult to debug.
- Handler ordering matters.
- Can be overkill for simple workflows.

## Interview Answer

> I use the Chain of Responsibility Pattern whenever a request needs to pass through multiple independent processing steps without coupling the caller to the entire workflow. Each handler owns a single responsibility and decides whether the request should continue. Middleware pipelines in FastAPI, Spring Boot, ASP.NET, and Express are excellent production examples.

## Related Patterns

| Pattern | Difference |
|----------|------------|
| Template Method | Fixed workflow with overridable steps. |
| Observer | Broadcasts events to all subscribers. |
| Command | Represents work as an object. |
| State | Changes behavior based on lifecycle. |

## Key Takeaways

- Build processing pipelines using independent handlers.
- Each handler knows only the next handler.
- Middleware is the canonical production example.
