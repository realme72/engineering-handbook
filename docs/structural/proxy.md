# Proxy Pattern

## Intent

The Proxy pattern introduces an object that sits between the client and the real object while exposing the same interface. Instead of the client communicating directly with the real object, every request passes through the proxy. This allows the proxy to transparently control access by performing operations such as authorization, caching, lazy intialization, rate limiting, or remote communication before delegating the request. The real object remains focused on business logic, while the proxy encapsulates all access-related concerns.

The primary goal of the Proxy Pattern is not to add new business functionality, but to separate access-control concerns from the core business logic while keeping the client completely unaware of the underlying implementation.


### What does the pattern do?

It introduces an intermediary object that controls access to another object while preserving the same interface.

### How does it work?

The client interacts only with the proxy. The proxy may perform additional checks, cache results, lazily initialize the real object, or even deny access before delegating the request.

### What structural problem does it solve?

It separates access-related concerns such as caching, authorization, lazy loading, and remote communication from the business logic, making the system easier to maintain and extend.

---

## Why Was This Pattern Introduced?

Consider a product catalog service.

Every request retrieves product details directly from the database.

```python
product = product_service.get_product(product_id)
```

Internally,

```text
Client

↓

Product Service

↓

Database
```

Now imagine thousands of users requesting the same product.

Every request results in another database query.

This creates unnecessary database load and increases response time.

A naive solution is to add caching directly inside the service.

```python
class ProductService:

    def get_product(self, product_id):

        if product_id in cache:
            return cache[product_id]

        product = database.fetch(product_id)

        cache[product_id] = product

        return product
```

Although this works, the service is now responsible for:

- Business Logic
- Caching
- Cache Management

This violates the Single Responsibility Principle.

The Proxy Pattern solves this by introducing a proxy that controls access to the real service.

```text
Client

↓

ProductServiceProxy

↓

ProductService

↓

Database
```

The proxy handles caching while the real service focuses only on business logic.

---

## Real-World Analogy

Imagine entering a corporate office.

You don't walk directly into the CEO's cabin.

Instead, you first interact with the receptionist.

The receptionist decides:

- Is the CEO available?
- Does the visitor have permission?
- Should the meeting be scheduled later?
- Should the visitor be redirected?

Only after these checks does the receptionist allow access.

The receptionist acts as the proxy.

---

## Software Engineering Example

One of the best examples of the Proxy Pattern is **Redis Cache**.

Without Proxy

```text
Client

↓

Product Service

↓

Database
```

Every request hits the database.

With Proxy

```text
Client

↓

Cache Proxy

↓

Cache Exists?

├── Yes
│
│   Return Cached Data
│
└── No
    │
    ▼
Product Service

↓

Database

↓

Store in Cache
```

The client never knows whether the data came from Redis or PostgreSQL.

Other production examples include:

- Redis Cache
- Nginx Reverse Proxy
- API Gateway
- Lazy Loading in ORMs
- Database Proxy
- Authorization Proxy
- Remote Service Proxy (RPC)

---

## Python Implementation

```python
from abc import ABC, abstractmethod


class ProductService(ABC):

    @abstractmethod
    def get_product(self, product_id):
        pass


class RealProductService(ProductService):

    def get_product(self, product_id):
        print("Fetching product from database...")
        return f"Product {product_id}"


class ProductServiceProxy(ProductService):

    def __init__(self):
        self.service = RealProductService()
        self.cache = {}

    def get_product(self, product_id):

        if product_id in self.cache:
            print("Returning product from cache...")
            return self.cache[product_id]

        product = self.service.get_product(product_id)

        self.cache[product_id] = product

        return product


service = ProductServiceProxy()

print(service.get_product(101))

print(service.get_product(101))
```

**Output**

```text
Fetching product from database...
Product 101

Returning product from cache...
Product 101
```

---

## Internal Workflow

When the client executes

```python
service.get_product(101)
```

the following sequence occurs.

```text
Client

        │

        ▼

ProductServiceProxy

        │

Cache Hit?

│

├── Yes

│     │

│     ▼

│ Return Cached Product

│

└── No

      │

      ▼

RealProductService

      │

      ▼

Database

      │

      ▼

Store in Cache

      │

      ▼

Return Product
```

The proxy determines whether the request should reach the real service.

The client remains unaware of this decision.

---

## How to Identify This Pattern

You are likely looking at a Proxy Pattern if you notice:

- A wrapper object exposing exactly the same interface as another object.
- The wrapper deciding whether or not to forward the request.
- Lazy object creation.
- Authorization checks before invoking the real object.
- Caching performed before calling the actual service.
- Remote communication hidden behind a local interface.

---

## Advantages

- ✅ Separates access control from business logic.
- ✅ Supports caching without modifying the original service.
- ✅ Enables lazy initialization.
- ✅ Improves security through authorization checks.
- ✅ Reduces unnecessary resource usage.

---

## Disadvantages

- ❌ Introduces additional classes.
- ❌ Adds another level of indirection.
- ❌ Can increase debugging complexity.
- ❌ Poorly designed proxies may become bottlenecks.

---

## When Should You Use It?

Use the Proxy Pattern when:

- Expensive objects should be created lazily.
- Access to an object needs authorization.
- Responses should be cached.
- Remote services should appear as local objects.
- Requests require monitoring or rate limiting.

---

## When Should You Avoid It?

Avoid the Proxy Pattern when:

- Direct access is acceptable.
- There is no additional access-related concern.
- The extra abstraction provides little value.
- Performance overhead from another layer outweighs the benefits.

---

## Common Interview Questions

### Basic

- What problem does the Proxy Pattern solve?
- How is Proxy different from Decorator?
- Why does Proxy expose the same interface as the real object?

### Intermediate

- What is a Virtual Proxy?
- What is a Remote Proxy?
- How does Redis caching relate to the Proxy Pattern?
- Where have you used the Proxy Pattern in production?

### Advanced

- Explain how Nginx acts as a Reverse Proxy.
- How does lazy loading in SQLAlchemy or Hibernate use the Proxy Pattern?
- Design an Authorization Proxy for an Admin Dashboard.
- How would you implement a thread-safe caching proxy?

---

## Related Patterns

| Pattern | Difference |
|----------|------------|
| Adapter | Adapter converts one interface into another. Proxy preserves the same interface while controlling access. |
| Decorator | Decorator adds new behavior. Proxy controls access to an existing object. |
| Facade | Facade simplifies a subsystem. Proxy controls access to a single object. |
| Bridge | Bridge separates abstraction from implementation. Proxy protects or manages access to an implementation. |

---

## Key Takeaways

- The Proxy Pattern introduces an intermediary object that sits between the client and the real object, controlling how and when requests are forwarded while preserving the same interface.
- The client interacts with the proxy instead of the real object.
- Proxies commonly implement caching, authorization, lazy loading, remote communication, and monitoring.
- The proxy preserves the same interface as the original object, making it transparent to clients.
- Redis, Nginx, API Gateways, ORM lazy loading, and database proxies are common production examples of the Proxy Pattern.