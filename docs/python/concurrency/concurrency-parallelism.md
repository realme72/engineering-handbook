# Concurrency vs Parallelism

## Concurrency

Concurrency is the ability to **make progress on multiple tasks during the same period of time.**

The tasks do **not** have to execute simultaneously.

Instead, the system switches between tasks whenever one task is waiting, allowing multiple tasks to progress together.

Imagine a backend server handling multiple API requests.

- Request 1 is waiting for PostgreSQL.
- While it's waiting, the CPU starts processing Request 2.
- When Request 2 waits for Redis, the CPU starts Request 3.

Even though only one request may be executing at a particular instant, all requests continue making progress.

Conceptually,

```
Time ───────────────────────────────────────────►

Request 1   ███ Waiting ███ Running ███ Done

Request 2        ███ Running ███ Waiting ███ Done

Request 3             ███ Running ███ Waiting ███ Done
```

The CPU stays busy by switching between tasks instead of waiting.

---

## Parallelism

Parallelism is the ability to execute multiple tasks **at exactly the same time.**

This requires multiple CPU cores or processors.

For example, on a machine with four CPU cores,

```
Core 1 → Request 1

Core 2 → Request 2

Core 3 → Request 3

Core 4 → Request 4
```

All four requests execute simultaneously.

No context switching is required because each task has its own CPU core.

---

## Concurrency vs Parallelism

```
Concurrency

        CPU

Task A ──────► Waiting
                 ▲
                 │
Task B ──────────┘
        │
        ▼
Task C

One CPU switches between multiple tasks.
```

```
Parallelism

Core 1 ───► Task A

Core 2 ───► Task B

Core 3 ───► Task C

Core 4 ───► Task D

Multiple CPU cores execute tasks simultaneously.
```

---

## Backend Example

Suppose your application receives **100 API requests**.

Each request performs the following operations.

- Read from PostgreSQL
- Read from Redis
- Call an external payment service

Most of the time is spent waiting for I/O.

### Without Concurrency

```
Request 1 -----------------------> Done

Request 2 -----------------------> Done

Request 3 -----------------------> Done
```

Every request waits for the previous one to finish.

---

### With Concurrency

```
Request 1  Waiting PostgreSQL

Request 2  Running

Request 3  Waiting Redis

Request 4  Running

Request 5  Waiting Payment API
```

Whenever one request waits for I/O, another request gets CPU time.

This improves resource utilization and increases throughput.

---

### With Parallelism

```
CPU Core 1 → Request 1

CPU Core 2 → Request 2

CPU Core 3 → Request 3

CPU Core 4 → Request 4
```

Multiple requests execute at the same time.

This is ideal for CPU-intensive workloads.

---

## When Should You Use Each?

### Concurrency

Best for I/O-bound tasks.

Examples:

- Web servers
- Database queries
- Network requests
- File I/O
- External APIs

---

### Parallelism

Best for CPU-bound tasks.

Examples:

- Image processing
- Video encoding
- Machine learning
- Mathematical computations
- Large data processing

---

## Relationship Between Them

Concurrency and parallelism are related but different concepts.

```
               Multiple Tasks
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
Concurrency                Parallelism

Makes progress             Executes tasks
on many tasks              simultaneously

May use                    Requires
one CPU                    multiple CPU cores
```

A concurrent program is not necessarily parallel.

A parallel program is usually concurrent because multiple tasks are progressing simultaneously.

---

## Follow-up Questions

### What is concurrency?

Concurrency is the ability to make progress on multiple tasks during the same period of time.

The tasks may execute by taking turns.

---

### What is parallelism?

Parallelism is the ability to execute multiple tasks simultaneously using multiple CPU cores.

---

### Does concurrency require multiple CPU cores?

No.

A single CPU can achieve concurrency by switching between tasks.

---

### Does parallelism require multiple CPU cores?

Yes.

True parallel execution requires multiple CPU cores or processors.

---

### Which is better for web servers?

Concurrency.

Web servers spend most of their time waiting for databases, APIs, or network responses.

---

### Which is better for CPU-intensive work?

Parallelism.

CPU-heavy tasks benefit from multiple CPU cores.

---

## Common Interview Mistakes

❌ Thinking concurrency means tasks execute simultaneously.

✔ Concurrency means multiple tasks make progress together.

---

❌ Thinking concurrency requires multiple CPU cores.

✔ A single CPU can achieve concurrency through task switching.

---

❌ Thinking parallelism is always faster.

✔ Parallelism helps only when the workload can effectively use multiple CPU cores.

---

## Interview Tip

A simple way to explain the difference is:

> **Concurrency is about dealing with multiple tasks at once.**

> **Parallelism is about executing multiple tasks at once.**

This distinction is easy to remember and is widely accepted in interviews.

---

## Key Takeaways

- Concurrency allows multiple tasks to make progress together.
- Parallelism executes multiple tasks simultaneously.
- Concurrency does not require multiple CPU cores.
- Parallelism requires multiple CPU cores.
- Concurrency is best suited for I/O-bound workloads.
- Parallelism is best suited for CPU-bound workloads.
- In Python, threads and `asyncio` provide concurrency, while multiprocessing provides true parallelism.