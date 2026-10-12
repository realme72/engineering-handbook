# Global Interpreter Lock (GIL) [Must Read ⭐ Master chapter]

## What is the GIL?

The **Global Interpreter Lock (GIL)** is a mutex (lock) used by the **CPython interpreter** that allows **only one thread to execute Python bytecode at a time within a single process**.

This means that even if a Python program creates multiple threads, only one of those threads can execute Python code at any given moment.

This behavior is specific to **CPython**, which is the default Python implementation.

---

## Before Understanding the GIL

Before understanding the GIL, let's connect it with everything we've already learned.

```
Python Objects
       │
       ▼
Memory Management
       │
       ▼
Reference Counting
       │
       ▼
Multiple Threads
       │
       ▼
Race Conditions
       │
       ▼
Global Interpreter Lock
```

The GIL exists because of **how CPython manages memory**.

If you understand memory management, the GIL becomes much easier to understand.

---

## Revisiting Memory Management

Recall the following example.

```python
a = []
b = a
```

Memory representation

```
a ─────┐
       │
       ▼
   List Object
       ▲
       │
b ─────┘

Reference Count = 2
```

Both variables point to the same list object.

Since two variables reference this object, its reference count is **2**.

Now suppose we execute

```python
a = None
```

Reference count becomes

```
Reference Count = 1
```

Later,

```python
b = None
```

Reference count becomes

```
Reference Count = 0
```

Python immediately frees the object.

Everything works correctly because these operations happen one after another.

---

## What Happens Without the GIL?

Now imagine two threads executing simultaneously.

Initially,

```
Reference Count = 2
```

Thread 1 executes

```python
a = None
```

At exactly the same time,

Thread 2 executes

```python
b = None
```

Both threads now try to modify the same reference count.

Conceptually,

```
Reference Count = 2

Thread 1 reads 2

Thread 2 reads 2

Thread 1 writes 1

Thread 2 writes 1
```

Final result

```
Reference Count = 1
```

But the correct result should have been

```
Reference Count = 0
```

Python now incorrectly believes the object is still being referenced.

The object is never freed.

This creates a **memory leak**.

---

## Even Worse...

The opposite problem can also happen.

Suppose the reference count reaches zero too early.

```
Thread 1 decreases reference count

Python frees the object

Thread 2 still tries to access the object
```

Conceptually,

```
Thread 1

Reference Count = 0

Free Object
```

Meanwhile,

```
Thread 2

Still accessing
the same object
```

The object no longer exists.

This leads to:

- Memory corruption
- Dangling references
- Program crashes
- Undefined behavior

This type of problem is called a **race condition**.

---

## What is a Race Condition?

A race condition occurs when two or more threads access and modify shared data simultaneously, causing unpredictable behavior.

Example

```
Shared Variable

count = 10


Thread 1
---------

count = count + 1


Thread 2
---------

count = count + 1
```

If both threads execute together,

```
Thread 1 reads 10

Thread 2 reads 10

Thread 1 writes 11

Thread 2 writes 11
```

Expected result

```
12
```

Actual result

```
11
```

One update is lost.

This is another example of a race condition.

---

## Why Does Python Have the GIL?

The primary reason is **memory safety**.

CPython uses **reference counting** to manage object lifetimes.

Without synchronization, multiple threads could modify reference counts simultaneously.

This would lead to:

- Incorrect reference counts
- Memory leaks
- Premature object deallocation
- Crashes
- Corrupted memory

Instead of protecting every Python object with individual locks, CPython uses one global lock.

That lock is the **Global Interpreter Lock**.

---

## How the GIL Solves This Problem

Instead of allowing every thread to execute Python bytecode simultaneously,

the GIL ensures that **only one thread owns the interpreter at a time**.

Conceptually,

```
                Python Process

          +-----------------------+
          |         GIL           |
          +-----------+-----------+
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
    Thread 1      Thread 2      Thread 3
```

Only one thread can hold the GIL.

Suppose Thread 1 acquires it.

```
Thread 1

Acquire GIL
      │
      ▼
Execute Python Code
      │
      ▼
Update Reference Counts
      │
      ▼
Release GIL
```

While Thread 1 owns the GIL,

```
Thread 2

Waiting...


Thread 3

Waiting...
```

Only after Thread 1 releases the GIL can another thread execute Python bytecode.

Because reference counts are updated one thread at a time, race conditions on Python objects are avoided.

---

## Important Clarification

The GIL does **not** mean only one thread exists.

A process can have hundreds of threads.

The GIL only guarantees that **one thread executes Python bytecode at any given moment.**

```
Python Process

        GIL
         │

  ┌──────┼──────────┐

Thread 1
Thread 2
Thread 3
Thread 4
Thread 5

Many threads exist.

Only one executes Python code at a time.
```

---

## Common Interview Questions

### What is the GIL?

The Global Interpreter Lock is a mutex in CPython that allows only one thread to execute Python bytecode at a time within a single process.

---

### Why does Python have the GIL?

CPython uses reference counting for memory management.

The GIL prevents multiple threads from simultaneously modifying Python objects and their reference counts, ensuring thread-safe memory management.

---

### Does every Python implementation have a GIL?

No.

The GIL is specific to **CPython**.

Other implementations may use different approaches.

---

### Does the GIL allow only one thread in a process?

No.

A process can create many threads.

The GIL only allows one thread to execute Python bytecode at a time.

---

### Does the GIL prevent race conditions completely?

No.

It protects Python's internal memory management.

Race conditions can still occur when multiple threads access shared application data.

We'll discuss this later in the Synchronization chapter.

---

## Why Doesn't Multithreading Speed Up CPU-Bound Programs?

Suppose we have the following function.

```python
def calculate():

    total = 0

    for i in range(1_000_000_000):
        total += i

    return total
```

Now create four threads.

```python
from threading import Thread

threads = []

for _ in range(4):
    t = Thread(target=calculate)
    threads.append(t)
    t.start()

for t in threads:
    t.join()
```

At first glance, it looks like all four threads should execute simultaneously.

However, because all threads belong to the **same Python process**, they also share the **same GIL**.

Conceptually,

```
                Python Process

          +-----------------------+
          |         GIL           |
          +-----------+-----------+
                      │
      ┌───────────────┼───────────────┐
      ▼               ▼               ▼

  Thread 1       Thread 2       Thread 3
      │               │               │
 Waiting         Waiting         Waiting
      ▲
      │
Executing Python Bytecode
```

Only one thread owns the GIL.

The remaining threads must wait.

Instead of executing simultaneously, the operating system repeatedly switches between them.

```
Time ---------------------------------------------------->

Thread 1   ████░░░░░░████░░░░░░████

Thread 2       ░░████░░░░████░░░░██

Thread 3           ░░░░████░░░░████
```

The CPU spends time switching between threads instead of performing useful work.

As a result, CPU-bound programs usually do **not** become faster with multithreading in CPython.

---

## Why Doesn't the GIL Affect I/O-bound Programs?

Now consider a web server.

Suppose a request performs the following operations.

```python
user = db.get_user()

orders = requests.get(order_service)

cache = redis.get("profile")
```

Most of the time, the CPU isn't executing Python code.

Instead, it's waiting for:

- Database responses
- Network responses
- Redis
- File I/O

Imagine Thread 1 executes.

```
Acquire GIL

↓

Execute Python

↓

requests.get(...)
```

At this point, the thread has nothing to compute.

It simply waits for the operating system to receive data from the network.

Keeping the GIL during this waiting period would waste CPU time.

Instead, CPython releases the GIL.

Conceptually,

```
Thread 1

Acquire GIL
      │
Execute Python
      │
requests.get()
      │
Release GIL
      │
Waiting for network
```

Now another thread immediately acquires the GIL.

```
Thread 2

Acquire GIL

↓

Execute Python

↓

db.get_user()

↓

Release GIL
```

Thread 2 can continue executing while Thread 1 waits.

Once Thread 1 receives its network response,

it competes for the GIL again and resumes execution.

---

## Timeline of Two Threads

```
Time ------------------------------------------------------------->

Thread 1

Acquire GIL
     │
Execute Python
     │
requests.get()
     │
Release GIL
     │
Waiting............................
                                │
                                ▼
                        Acquire GIL Again
                                │
                           Continue Execution



Thread 2

                Waiting
                    │
                    ▼
              Acquire GIL
                    │
             Execute Python
                    │
             redis.get()
                    │
             Release GIL
```

Notice something important.

Only one thread executes Python bytecode at any instant.

However,

while one thread waits for I/O,

another thread keeps the CPU busy.

This is why multithreading is extremely effective for web applications.

---

## When Does CPython Release the GIL?

CPython automatically releases the GIL during blocking I/O operations.

Examples include:

- Reading files
- Writing files
- Database queries
- HTTP requests
- Socket communication
- Sleeping (`time.sleep()`)
- Waiting for external APIs

Example

```python
import requests

response = requests.get("https://example.com")
```

During the network request,

the current thread releases the GIL,

allowing another thread to execute Python code.

---

## CPU-bound vs I/O-bound

Understanding this distinction is one of the most common interview questions.

### CPU-bound

The CPU spends most of its time performing computations.

Examples:

- Image processing
- Video encoding
- Mathematical computations
- Data compression
- Machine learning

```
CPU

██████████████████████████████████

Always Busy
```

Threads do not help much here because they compete for the same GIL.

---

### I/O-bound

The CPU spends most of its time waiting.

Examples:

- Database queries
- REST APIs
- Reading files
- Redis
- Kafka
- RabbitMQ

```
CPU

██ Waiting ███ Waiting ███ Waiting
```

Since threads release the GIL while waiting,

other threads continue executing.

This significantly improves throughput.

---

## Why Are Web Servers Usually Multithreaded?

A common interview question is:

> If only one thread executes Python bytecode, why do web servers still use threads?

The answer is that web applications are primarily **I/O-bound**.

A request spends far more time waiting than computing.

For example,

```
Receive Request

↓

Execute Python

↓

Query PostgreSQL

↓

Waiting...

↓

Receive Data

↓

Call Payment Service

↓

Waiting...

↓

Return Response
```

Most of the request lifetime is spent waiting for external systems.

While one thread waits,

another thread can execute.

This keeps the CPU busy and improves the overall throughput of the application.

---

## Common Interview Questions

### Why doesn't multithreading improve CPU-bound programs?

Because only one thread executes Python bytecode at a time due to the GIL.

The threads compete for the same interpreter lock.

---

### Why does multithreading improve web applications?

Because blocking I/O operations release the GIL.

While one thread waits,

another thread executes Python code.

---

### Does the GIL slow down every multithreaded program?

No.

It mainly limits CPU-bound programs.

I/O-bound programs still benefit significantly from multithreading.

---

## Mental Model

```
                CPU-bound

          Needs CPU Computation

                    │

                    ▼

           GIL becomes bottleneck

                    │

          Multiprocessing wins



--------------------------------------------



                I/O-bound

       Waiting for external resources

                    │

                    ▼

        GIL released during waiting

                    │

                    ▼

      Multithreading performs well
```

---

## How Does Multiprocessing Solve the GIL Problem?

We've learned that the GIL is **one lock per Python process**.

This naturally raises an important question.

> If only one thread can execute Python bytecode at a time, how do Python applications utilize multiple CPU cores?

The answer is **multiprocessing**.

Instead of creating multiple threads inside one process,

Python creates multiple independent processes.

Each process has:

- Its own Python interpreter
- Its own memory
- Its own GIL

Conceptually,

```
                 CPU

        ┌────────┼────────┬────────┐
        ▼        ▼        ▼        ▼

    Process 1 Process 2 Process 3 Process 4

       GIL       GIL       GIL       GIL
        │         │         │         │
    Thread(s) Thread(s) Thread(s) Thread(s)
```

Since every process owns its own interpreter,

each process can execute Python bytecode simultaneously.

This achieves **true parallelism**.

---

## Threads vs Processes

This is probably the most frequently asked interview question after the GIL.

```
                    Threads

          One Process
                │
      ┌─────────┼─────────┐
      ▼         ▼         ▼
  Thread 1  Thread 2  Thread 3

      Shared Memory
      Shared GIL
```

```
                  Processes

 Process 1    Process 2    Process 3

    │             │             │

 Own Memory   Own Memory   Own Memory

 Own GIL      Own GIL      Own GIL
```

### Thread Characteristics

- Lightweight
- Fast to create
- Share memory
- Share the GIL
- Excellent for I/O-bound work

---

### Process Characteristics

- Heavyweight
- Separate memory
- Own Python interpreter
- Own GIL
- Excellent for CPU-bound work

---

## Why Don't Processes Share Memory?

Suppose Process 1 accidentally crashes.

```
Process 1

Segmentation Fault
```

Processes 2 and 3 continue running.

```
Process 2

Still Running


Process 3

Still Running
```

This isolation is one of the biggest advantages of multiprocessing.

---

## Example

CPU-intensive work

```python
def calculate():

    total = 0

    for i in range(1_000_000_000):
        total += i
```

Using threads

```
CPU

Thread 1

Thread 2

Thread 3

↓

One GIL

↓

One thread executes at a time
```

Using processes

```
Core 1 → Process 1

Core 2 → Process 2

Core 3 → Process 3

Core 4 → Process 4
```

Now all CPU cores perform computation simultaneously.

---

## How Does FastAPI Handle Requests?

Many developers think:

```
One Request

↓

One Thread
```

This is **not true** for asynchronous FastAPI applications.

FastAPI is built on top of **ASGI**.

Most deployments use

```
FastAPI

↓

Uvicorn

↓

AsyncIO Event Loop
```

A typical worker looks like this.

```
            One Process

                 │

              One GIL

                 │

            One Thread

                 │

           Event Loop

                 │

   ┌─────────────┼─────────────┐

   ▼             ▼             ▼

Coroutine 1  Coroutine 2  Coroutine 3
```

Notice something interesting.

There is only

- One thread
- One GIL

Yet thousands of requests can be handled concurrently.

How?

Because the event loop schedules **coroutines**, not threads.

---

## What Happens During a Request?

Suppose an endpoint executes

```python
@app.get("/users")
async def get_users():

    user = await db.fetch_user()

    return user
```

Execution

```
Request arrives

↓

Coroutine starts

↓

await db.fetch_user()

↓

Coroutine pauses

↓

Event Loop schedules another coroutine
```

The thread never blocks.

Instead,

another coroutine immediately begins executing.

---

## Event Loop Scheduling

Imagine three requests arrive.

```
Request 1

↓

await PostgreSQL

↓

Waiting



Request 2

↓

Running



Request 3

↓

await Redis

↓

Waiting
```

Instead of blocking,

the event loop simply switches to another coroutine.

Conceptually,

```
Time -------------------------------------------------->

Coroutine 1

Running

↓

await Database

↓

Waiting.....................

↓

Running Again



Coroutine 2

Running

↓

await Redis

↓

Waiting.................

↓

Running Again



Coroutine 3

Running

↓

Finished
```

Notice something important.

No operating system thread switching occurs.

The **event loop** performs cooperative scheduling between coroutines.

This makes context switching significantly cheaper than thread switching.

---

## Scaling FastAPI

One worker

```
FastAPI

↓

1 Process

↓

1 Event Loop

↓

Thousands of Coroutines
```

Using

```bash
uvicorn app:app --workers 4
```

creates

```
                 Load Balancer

                       │

        ┌──────────────┼──────────────┐

        ▼              ▼              ▼

   Worker 1      Worker 2      Worker 3      Worker 4

    Process        Process        Process       Process

      GIL            GIL            GIL           GIL

   Event Loop    Event Loop    Event Loop   Event Loop

 Thousands of   Thousands of   Thousands   Thousands
 Coroutines     Coroutines     Coroutines  Coroutines
```

Each worker is an independent process.

Each worker has

- Its own interpreter
- Its own GIL
- Its own event loop

This allows FastAPI to scale across multiple CPU cores while still benefiting from asynchronous concurrency inside each worker.

---

## Mental Model

```
                   Python Concurrency


                 CPU-bound Work

                       │

                Multiprocessing

                       │

          Multiple Processes

                       │

          Multiple Python Interpreters

                       │

                 Multiple GILs

                       │

                True Parallelism



----------------------------------------------------



                  I/O-bound Work

                        │

                  AsyncIO / Threads

                        │

               One Python Process

                        │

                     One GIL

                        │

       Switch while waiting for I/O

                        │

            High Concurrency
```

---

## Thread Pool in FastAPI

Earlier we learned that an asynchronous FastAPI application usually runs on:

```
One Process
      │
One Thread
      │
Event Loop
      │
Coroutines
```

This works well for asynchronous code.

However, what happens if we call a blocking synchronous function?

```python
@app.get("/users")
async def get_users():

    users = fetch_users_from_legacy_system()

    return users
```

Suppose `fetch_users_from_legacy_system()` performs a blocking network call.

The event loop now waits until the function returns.

While waiting,

no other coroutine can execute.

This blocks the entire event loop.

---

## The Solution

Instead of executing the blocking function directly,

FastAPI executes it inside a thread pool.

Conceptually,

```
                 Event Loop

                      │

       Blocking Function Detected

                      │

                      ▼

               Thread Pool

         ┌────────┬────────┬────────┐

         ▼        ▼        ▼

     Thread1  Thread2  Thread3
```

The event loop immediately continues scheduling other coroutines.

Meanwhile,

the blocking function executes in a background thread.

When it finishes,

the result is returned to the coroutine.

---

## Decision Tree

One of the most common senior-level interview questions is:

> Which concurrency model would you choose?

Think about it like this.

```
                    New Problem

                         │

               Is it CPU-bound?

                  ┌──────┴──────┐

                 Yes            No

                  │              │

        Multiprocessing    Is it I/O-bound?

                               │

                    ┌───────────┴────────────┐

                   Yes                      No

                    │

        Does the library support async?

               ┌────┴─────┐

              Yes         No

              │            │

          AsyncIO     Multithreading
```

This simple decision tree answers most interview questions.

---

## Threads vs Processes vs AsyncIO

| Feature | Multithreading | Multiprocessing | AsyncIO |
|----------|---------------|----------------|----------|
| Uses multiple threads | ✅ | ❌ | ❌ |
| Uses multiple processes | ❌ | ✅ | ❌ |
| Uses Event Loop | ❌ | ❌ | ✅ |
| Shared Memory | ✅ | ❌ | ✅ |
| Separate GIL | ❌ | ✅ | ❌ |
| True Parallelism | ❌ | ✅ | ❌ |
| Best For | I/O-bound | CPU-bound | Massive I/O |
| Context Switch Cost | Medium | High | Very Low |

---

## When Should You Use Each?

### Use Multithreading

When

- Database queries
- REST APIs
- Reading files
- Kafka consumers
- RabbitMQ consumers
- Legacy synchronous libraries

---

### Use Multiprocessing

When

- Image processing
- Machine learning
- Data processing
- Mathematical computation
- Compression
- Video encoding

---

### Use AsyncIO

When

- FastAPI
- Starlette
- Async database drivers
- High-concurrency web servers
- Thousands of simultaneous connections
- WebSockets

---

## Complete Picture

```
                   Python Process

                         │

                        GIL

                         │

      ┌──────────────────┼─────────────────┐

      ▼                  ▼                 ▼

 Threads           Event Loop        Background Tasks

      │                  │

      │             Coroutines

      │                  │

      └──────────────┬───┘

                     ▼

               I/O Concurrency


=====================================================


             Multiple Python Processes

      ┌────────────┬────────────┬────────────┐

      ▼            ▼            ▼

 Process 1    Process 2    Process 3

     GIL          GIL          GIL

 True Parallel Execution
```

---

## Common Interview Questions

### What is the GIL?

The Global Interpreter Lock is a mutex in CPython that allows only one thread to execute Python bytecode at a time within a single process.

---

### Why does Python need the GIL?

CPython uses reference counting for memory management.

The GIL prevents multiple threads from modifying Python objects simultaneously, making memory management thread-safe.

---

### Does the GIL make Python single-threaded?

No.

Python can create multiple threads.

The GIL only ensures that one thread executes Python bytecode at a time.

---

### Why doesn't multithreading speed up CPU-bound programs?

Because all threads compete for the same GIL.

Only one thread executes Python bytecode at any instant.

---

### Why do web servers still use multithreading?

Blocking I/O operations release the GIL.

While one thread waits for I/O,

another thread executes Python code.

---

### How does multiprocessing bypass the GIL?

Each process has:

- Its own interpreter
- Its own memory
- Its own GIL

Multiple processes execute simultaneously on different CPU cores.

---

### Does AsyncIO remove the GIL?

No.

AsyncIO still runs inside a single Python process.

It doesn't bypass the GIL.

Instead,

it avoids blocking by switching between coroutines whenever one performs an `await`.

---

### Which is faster: Threads or AsyncIO?

There isn't a universal answer.

- Threads are useful for blocking synchronous code.
- AsyncIO is usually more scalable for asynchronous I/O because coroutine switching is cheaper than thread switching.

---

### Can I combine all three?

Yes.

A production FastAPI deployment commonly looks like this.

```
                 Load Balancer

                       │

         ┌─────────────┼─────────────┐

         ▼             ▼             ▼

    Worker 1      Worker 2      Worker 3

      Process        Process        Process

         │              │              │

    Event Loop     Event Loop     Event Loop

         │              │              │

 Thousands of     Thousands of     Thousands of
 Coroutines       Coroutines       Coroutines

         │

 Blocking Work

         ▼

 Thread Pool
```

This combines:

- Multiprocessing
- AsyncIO
- Multithreading

into one scalable architecture.

---

## Common Interview Mistakes

❌ Thinking the GIL allows only one thread in Python.

✔ The GIL allows only one thread to execute Python bytecode at a time **per process**.

---

❌ Thinking the GIL affects multiprocessing.

✔ Every process has its own interpreter and its own GIL.

---

❌ Thinking AsyncIO bypasses the GIL.

✔ AsyncIO achieves concurrency through cooperative scheduling, not parallel execution.

---

❌ Using threads for CPU-intensive work.

✔ Use multiprocessing for CPU-bound workloads.

---

❌ Thinking web servers are CPU-bound.

✔ Most backend applications spend the majority of their time waiting for databases, caches, message brokers, or external APIs.

---

## Interview Tip

When asked,

> "Explain the GIL."

Don't stop after saying:

> "Only one thread executes Python bytecode."

A stronger answer is:

> "CPython uses reference counting for memory management. Without synchronization, multiple threads could corrupt reference counts, causing race conditions, memory leaks, or premature object deallocation. The GIL prevents this by ensuring only one thread executes Python bytecode at a time within a process. Although this limits CPU-bound multithreading, the GIL is released during blocking I/O operations, which is why multithreading still improves the performance of web applications."

This answer explains not only **what** the GIL is, but also **why it exists** and **when it matters**.

---

## Key Takeaways

- The GIL is a mutex used by CPython.
- There is **one GIL per Python process**.
- Threads within a process share the same GIL.
- The GIL protects CPython's reference-counting memory management.
- CPU-bound programs should use **multiprocessing**.
- I/O-bound programs benefit from **multithreading** because blocking I/O releases the GIL.
- AsyncIO provides concurrency using an event loop and coroutines, not additional threads.
- Modern FastAPI applications typically combine **multiprocessing**, **AsyncIO**, and **thread pools** for maximum scalability.