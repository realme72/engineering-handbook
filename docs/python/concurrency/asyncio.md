# AsyncIO

## Why Do We Need AsyncIO?

Let's start with a common backend application.

Suppose a FastAPI endpoint performs the following operations.

```python
user = db.fetch_user()

orders = payment_service.get_orders()

inventory = redis.get()
```

None of these operations are CPU-intensive.

Instead, they spend most of their time waiting for external systems.

- PostgreSQL
- Redis
- Payment APIs
- File System
- Network

Conceptually,

```
Request

↓

Execute Python

↓

Query Database

↓

Waiting...

↓

Receive Data

↓

Call Payment API

↓

Waiting...

↓

Return Response
```

Notice something.

The CPU is idle while waiting for the database or network.

This is wasted CPU time.

---

## Can Threads Solve This?

Yes.

Multithreading improves I/O-bound workloads because when one thread waits for I/O, another thread can execute.

```
Thread 1

↓

Waiting for PostgreSQL

-----------------------

Thread 2

↓

Executing Python
```

However,

threads are not free.

Every thread requires:

- Stack Memory
- Registers
- Operating System Scheduling
- Context Switching

Creating thousands of threads becomes expensive.

Imagine handling 20,000 concurrent users.

```
20,000 Requests

↓

20,000 Threads
```

This quickly consumes memory and increases context-switching overhead.

There must be a more efficient solution.

---

## The Idea Behind AsyncIO

Instead of creating one thread per request,

what if a **single thread** could handle thousands of waiting operations?

```
                 One Thread

                      │

        ┌─────────────┼─────────────┐

        ▼             ▼             ▼

    Request 1     Request 2     Request 3
```

Whenever one request starts waiting for I/O,

the thread immediately begins executing another request.

The thread never sits idle.

This is exactly what AsyncIO does.

---

## The Missing Piece

Imagine three requests arrive.

```
Request 1

↓

Query PostgreSQL

↓

Waiting...
```

```
Request 2

↓

Call Payment API

↓

Waiting...
```

```
Request 3

↓

Read Redis

↓

Waiting...
```

Question:

Who decides

> "Request 2 can execute now."

Who pauses Request 1?

Who resumes Request 3?

Something has to coordinate all these requests.

That component is called the **Event Loop**.

---

# What is an Event Loop?

The **Event Loop** is the heart of AsyncIO.

It is responsible for:

- Scheduling coroutines
- Pausing them when they wait for I/O
- Resuming them when the I/O completes

Think of it as a scheduler.

Instead of scheduling threads,

it schedules **coroutines**.

```
              Event Loop

                    │

      ┌─────────────┼─────────────┐

      ▼             ▼             ▼

 Coroutine 1   Coroutine 2   Coroutine 3
```

The event loop constantly checks which coroutine is ready to execute.

---

## A Simple Analogy

Imagine a chef cooking three dishes.

Without AsyncIO,

the chef behaves like this.

```
Cook Pasta

↓

Wait for Water

↓

Stand Idle

↓

Water Boils

↓

Continue Cooking
```

Most of the chef's time is wasted waiting.

Now imagine a smarter chef.

```
Boil Pasta

↓

While Waiting

↓

Prepare Salad

↓

While Waiting

↓

Bake Pizza

↓

Pasta Ready

↓

Continue Cooking
```

The chef never sits idle.

The event loop works in the same way.

Whenever one coroutine waits,

the event loop immediately switches to another coroutine that is ready to execute.

---

## Event Loop Execution

Suppose three requests arrive.

Initially,

```
Request 1

Running
```

Then,

```
Request 1

↓

Database Query

↓

Waiting...
```

The event loop immediately switches.

```
Request 2

Running
```

Now Request 2 calls an external API.

```
Request 2

↓

Waiting...
```

The event loop switches again.

```
Request 3

Running
```

Eventually,

the database response for Request 1 arrives.

The operating system notifies the event loop.

The event loop simply resumes Request 1.

Conceptually,

```
Time -------------------------------------------------->

Request 1

Running

↓

Waiting Database

↓

Running Again

↓

Finished



Request 2

Running

↓

Waiting API

↓

Running Again

↓

Finished



Request 3

Running

↓

Finished
```

Notice something important.

Only **one thread** exists.

The event loop simply decides which coroutine should execute next.

---

## Where Does the Operating System Come In?

The event loop does not continuously ask,

"Is the database ready?"

That would waste CPU cycles.

Instead,

the operating system notifies the event loop whenever an I/O operation completes.

Conceptually,

```
Coroutine

↓

Starts Database Query

↓

Operating System

↓

Waiting...

↓

Database Responds

↓

Operating System

↓

Event Loop Notified

↓

Coroutine Resumes
```

The event loop only wakes up coroutines that are ready to continue.

---

## What is a Coroutine?

We've been mentioning coroutines,

but what exactly are they?

A **coroutine** is a function whose execution can be paused and resumed.

Unlike a normal function,

a coroutine doesn't have to run from start to finish in one go.

Instead,

it can temporarily give control back to the event loop while waiting for an operation to complete.

Conceptually,

```
Coroutine

↓

Execute

↓

Pause

↓

Resume

↓

Pause

↓

Resume

↓

Finish
```

We'll see exactly how this happens using `async` and `await` in the next section.

---

## Threads vs Coroutines

```
Threads

Operating System

↓

Schedules Threads

↓

Context Switch

↓

Higher Overhead
```

```
Coroutines

Event Loop

↓

Schedules Coroutines

↓

Very Lightweight

↓

Low Overhead
```

This is why a single thread can efficiently manage thousands of coroutines.

---

## Mental Model

```
                 Incoming Requests

                        │

                        ▼

                  Event Loop

                        │

        ┌───────────────┼───────────────┐

        ▼               ▼               ▼

   Coroutine 1     Coroutine 2     Coroutine 3

        │               │               │

     Waiting         Running        Waiting

        ▲                               │

        └───────────────Ready───────────┘
```

The event loop always runs whichever coroutine is ready.

No CPU time is wasted waiting.

---

## Common Interview Questions

### Why do we need AsyncIO?

AsyncIO allows a single thread to efficiently handle many concurrent I/O-bound operations by switching between coroutines whenever one is waiting.

---

### What is an Event Loop?

The Event Loop is the scheduler responsible for executing, pausing, and resuming coroutines.

---

### Does AsyncIO create multiple threads?

No.

By default, AsyncIO runs on a single thread.

---

### What is a Coroutine?

A coroutine is a function that can pause its execution and later resume from the same point.

---

## Key Takeaways

- AsyncIO is designed for I/O-bound concurrency.
- Instead of creating many threads, AsyncIO uses a single event loop.
- The event loop schedules coroutines.
- Coroutines pause while waiting for I/O and resume when the operation completes.
- The operating system notifies the event loop when I/O is ready.
- A single thread can efficiently manage thousands of concurrent coroutines.

---

## Creating a Coroutine

In the previous section, we learned that the event loop schedules **coroutines**.

But how are coroutines created?

Python creates a coroutine using the `async` keyword.

```python
async def fetch_user():
    print("Fetching user...")
```

This looks similar to a normal function,

but it behaves very differently.

---

## Normal Function vs Coroutine Function

Normal function

```python
def greet():
    print("Hello")
```

Calling it

```python
greet()
```

Immediately executes the function.

```
Call Function

↓

Execute

↓

Return
```

---

Coroutine function

```python
async def fetch_user():
    print("Fetching...")
```

Calling it

```python
fetch_user()
```

does **not** execute the function.

Instead,

Python creates a **coroutine object**.

```
fetch_user()

↓

Coroutine Object Created

↓

Returned to Caller
```

Nothing inside the function executes yet.

---

## Everything is an Object

Earlier in this handbook we learned:

- Integers are objects
- Lists are objects
- Functions are objects

Coroutines are objects too.

```python
async def fetch():

    return "Hello"

coro = fetch()

print(type(coro))
```

Output

```python
<class 'coroutine'>
```

Conceptually,

```
fetch

↓

Coroutine Object

↓

Waiting to Execute
```

The coroutine object contains everything required to execute the function later.

---

## Why Doesn't It Execute Immediately?

Suppose we have

```python
async def fetch():

    print("Start")

fetch()
```

Output

```
Nothing
```

Why?

Because no event loop is running the coroutine.

Creating a coroutine object is similar to writing down a task.

It doesn't begin until someone starts working on it.

The event loop is responsible for executing coroutine objects.

---

## Executing a Coroutine

The simplest way is

```python
import asyncio

async def greet():

    print("Hello")

asyncio.run(greet())
```

Execution

```
greet()

↓

Coroutine Object

↓

asyncio.run()

↓

Event Loop Starts

↓

Coroutine Executes

↓

Event Loop Stops
```

Output

```
Hello
```

---

## What Does asyncio.run() Do?

`asyncio.run()` performs three important steps.

```
Create Event Loop

↓

Run Coroutine

↓

Close Event Loop
```

Conceptually,

```
Coroutine

↓

Event Loop

↓

Execute

↓

Finished

↓

Event Loop Closed
```

In real applications like FastAPI,

you never call `asyncio.run()` yourself.

The framework already has a running event loop.

---

# Understanding await

The `await` keyword is the most important concept in AsyncIO.

Suppose we have

```python
async def fetch_user():

    await db.fetch()

    print("Done")
```

What happens?

Execution begins normally.

```
Coroutine Starts

↓

Execute Python
```

Eventually,

it reaches

```python
await db.fetch()
```

At this point,

the database query has been sent.

The coroutine has nothing else to do.

Instead of blocking the thread,

it voluntarily pauses.

```
Coroutine

↓

await

↓

Pause

↓

Return Control

↓

Event Loop
```

The event loop immediately schedules another coroutine.

---

## Visualizing await

Imagine three requests.

```
Coroutine 1

↓

await PostgreSQL

↓

Paused
```

Immediately,

```
Coroutine 2

↓

Running
```

Later,

```
Database Responds

↓

Event Loop Notified

↓

Coroutine 1 Resumes
```

The coroutine continues exactly where it stopped.

---

## await Does NOT Create a Thread

A common misconception is that

```python
await
```

creates another thread.

It does not.

```
One Thread

↓

Event Loop

↓

Coroutine 1

↓

Coroutine 2

↓

Coroutine 3
```

Everything still executes on the same thread.

The only difference is that coroutines voluntarily give up execution while waiting.

---

## Coroutine Lifecycle

```
Coroutine Created

↓

Scheduled by Event Loop

↓

Running

↓

await

↓

Paused

↓

Waiting for I/O

↓

Operating System Signals Completion

↓

Event Loop Resumes Coroutine

↓

Running

↓

Finished
```

This lifecycle repeats until the coroutine completes.

---

## Putting Everything Together

Suppose we have

```python
async def get_user():

    user = await db.fetch()

    return user
```

Conceptually,

```
HTTP Request

↓

Coroutine Created

↓

Event Loop Schedules Coroutine

↓

Coroutine Starts

↓

await db.fetch()

↓

Coroutine Pauses

↓

Database Query Running

↓

Database Responds

↓

Operating System Notification

↓

Event Loop Resumes Coroutine

↓

Return User

↓

HTTP Response
```

Notice something.

At no point was another thread created.

The event loop simply paused and resumed the coroutine.

---

## Coroutines vs Threads

```
Thread

Running

↓

Blocked

↓

Operating System Context Switch

↓

Another Thread Runs
```

```
Coroutine

Running

↓

await

↓

Coroutine Pauses

↓

Event Loop Chooses Another Coroutine
```

Coroutine switching is much cheaper because no operating system thread switch occurs.

---

## Common Interview Questions

### What is a coroutine?

A coroutine is a function whose execution can be paused and resumed. Calling an `async` function creates a coroutine object.

---

### Does calling an async function execute it?

No.

Calling an async function creates a coroutine object.

The coroutine executes only when scheduled by the event loop.

---

### What does `await` do?

`await` pauses the current coroutine until the awaited operation completes and returns control to the event loop so other coroutines can execute.

---

### Does `await` block the thread?

No.

It suspends only the current coroutine.

The event loop continues executing other ready coroutines.

---

### Does `await` create another thread?

No.

Everything still executes on the same thread unless threads are explicitly created.

---

## Common Interview Mistakes

❌ Thinking `async def` immediately executes.

✔ It creates a coroutine function.

---

❌ Thinking calling an async function starts execution.

✔ It creates a coroutine object.

---

❌ Thinking `await` blocks the thread.

✔ It suspends only the current coroutine.

---

❌ Thinking AsyncIO creates threads automatically.

✔ AsyncIO achieves concurrency using an event loop and coroutines, not additional threads.

---

## Key Takeaways

- `async def` defines a coroutine function.
- Calling an async function creates a coroutine object.
- Coroutines are first-class Python objects.
- Coroutines execute only when scheduled by the event loop.
- `await` pauses the current coroutine without blocking the thread.
- While one coroutine waits, the event loop schedules another coroutine.
- AsyncIO achieves concurrency using cooperative scheduling rather than multiple threads.

---

## Coroutines Are Passive

So far we've learned that calling an async function creates a coroutine object.

```python
async def fetch():
    print("Fetching...")

coro = fetch()
```

Conceptually,

```
fetch()

↓

Coroutine Object

↓

Waiting to Execute
```

Notice something important.

The coroutine is **passive**.

It simply exists.

It is **not** executing yet.

Someone has to tell the event loop,

> "Please schedule this coroutine."

That is the job of a **Task**.

---

# What is a Task?

A **Task** is a wrapper around a coroutine.

It tells the event loop,

> "Schedule this coroutine and manage its execution."

Think of it like this.

```
Coroutine

↓

Task

↓

Event Loop

↓

Execution
```

Without a Task,

a coroutine is simply an object.

With a Task,

the coroutine becomes something the event loop actively executes.

---

## Creating a Task

Python provides

```python
asyncio.create_task()
```

Example

```python
import asyncio

async def fetch():

    print("Fetching...")

async def main():

    task = asyncio.create_task(fetch())

    await task

asyncio.run(main())
```

Execution

```
Coroutine Created

↓

Task Created

↓

Registered with Event Loop

↓

Event Loop Executes Task
```

Output

```
Fetching...
```

---

## Why Do We Need Tasks?

Suppose we write

```python
await fetch()

await process()
```

Execution

```
fetch()

↓

Wait

↓

process()
```

Only after `fetch()` finishes does `process()` begin.

This is still sequential.

---

Now consider

```python
task1 = asyncio.create_task(fetch())

task2 = asyncio.create_task(process())

await task1

await task2
```

Execution

```
Event Loop

↓

Task 1

↓

Task 2

↓

Runs both whenever they're ready
```

Both tasks are scheduled immediately.

Whenever one task reaches an `await`,

the event loop switches to the other.

---

## Task Lifecycle

```
Coroutine Created

↓

Task Created

↓

Scheduled

↓

Running

↓

Paused (await)

↓

Running

↓

Completed
```

The Task keeps track of the coroutine's state throughout its lifetime.

---

# What is a Future?

A **Future** represents a value that is not available yet but will become available later.

Think of it as a placeholder.

```
Current Time

↓

Future

↓

Result Arrives Later
```

Example

```
Database Query

↓

Future

↓

Database Responds

↓

Result Available
```

A Task is actually built on top of a Future.

Conceptually,

```
Future

↓

Task

↓

Coroutine
```

The Task executes the coroutine and stores its eventual result inside the Future.

---

## Relationship Between Them

```
async def fetch()

        │

Creates

        ▼

Coroutine

        │

Wrapped By

        ▼

Task

        │

Managed By

        ▼

Event Loop

        │

Produces

        ▼

Future Result
```

This relationship is frequently asked in senior interviews.

---

# Running Multiple Coroutines

Suppose we have

```python
async def fetch_user():

    ...

async def fetch_orders():

    ...

async def fetch_inventory():

    ...
```

If we write

```python
await fetch_user()

await fetch_orders()

await fetch_inventory()
```

Execution

```
User

↓

Orders

↓

Inventory
```

Everything runs sequentially.

---

Instead,

create Tasks.

```python
user = asyncio.create_task(fetch_user())

orders = asyncio.create_task(fetch_orders())

inventory = asyncio.create_task(fetch_inventory())

await user
await orders
await inventory
```

Execution

```
Event Loop

↓

User

Orders

Inventory

↓

Switches whenever one waits
```

Now all three operations make progress concurrently.

---

# asyncio.gather()

Creating many tasks manually becomes repetitive.

Instead,

Python provides

```python
asyncio.gather()
```

Example

```python
results = await asyncio.gather(

    fetch_user(),

    fetch_orders(),

    fetch_inventory()

)
```

Conceptually,

```
Coroutine 1

Coroutine 2

Coroutine 3

↓

gather()

↓

Schedule Together

↓

Wait Until All Complete

↓

Return Results
```

The returned list preserves the order of the supplied coroutines.

---

## gather() vs create_task()

Both execute coroutines concurrently,

but they have different purposes.

### create_task()

```
Coroutine

↓

Task

↓

Runs Independently
```

Useful when you want the coroutine to continue running in the background.

---

### gather()

```
Coroutine 1

Coroutine 2

Coroutine 3

↓

Run Together

↓

Wait For All

↓

Collect Results
```

Useful when you need all results before continuing.

---

## Example

```python
async def fetch_user():

    return "User"

async def fetch_orders():

    return "Orders"

async def main():

    result = await asyncio.gather(

        fetch_user(),

        fetch_orders()

    )

    print(result)

asyncio.run(main())
```

Output

```
['User', 'Orders']
```

---

## Common Interview Questions

### What is a Task?

A Task is a wrapper around a coroutine that schedules it for execution by the event loop.

---

### What is a Future?

A Future is a placeholder for a value that will become available later.

---

### Difference between Coroutine and Task?

A coroutine defines the work.

A Task schedules and manages the execution of that coroutine.

---

### What is asyncio.create_task()?

It wraps a coroutine into a Task and schedules it to run on the event loop.

---

### What is asyncio.gather()?

It schedules multiple coroutines concurrently and waits until all of them complete.

---

### Does create_task() immediately execute the coroutine?

Not exactly.

It schedules the coroutine.

The event loop decides when it actually runs.

---

## Common Interview Mistakes

❌ Thinking coroutines execute immediately.

✔ Coroutines execute only after being scheduled by the event loop.

---

❌ Thinking a Task is another thread.

✔ A Task is simply a scheduled coroutine.

---

❌ Thinking gather() creates threads.

✔ gather() schedules multiple coroutines on the same event loop.

---

## Mental Model

```
async def

      │

      ▼

Coroutine

      │

create_task()

      ▼

Task

      │

Event Loop

      ▼

Running

      │

await

      ▼

Paused

      │

Resume

      ▼

Completed

      │

Future Holds Result
```

---

## Key Takeaways

- Calling an async function creates a coroutine object.
- Coroutines are passive until scheduled.
- A Task wraps and schedules a coroutine for execution.
- The Event Loop manages Task execution.
- A Future represents a result that will be available later.
- `create_task()` schedules a coroutine to run concurrently.
- `gather()` schedules multiple coroutines and waits for all of them to finish.

---

## How Does FastAPI Handle Thousands of Requests?

One of the most common interview questions is:

> **If FastAPI runs on a single thread, how can it handle thousands of concurrent requests?**

Let's walk through the complete request lifecycle.

Suppose a client sends an HTTP request.

```
Browser

↓

GET /users
```

The request reaches the ASGI server (typically Uvicorn).

```
Client

↓

Uvicorn

↓

Event Loop
```

Uvicorn creates a coroutine for the request and schedules it on the event loop.

Suppose our endpoint is

```python
@app.get("/users")
async def get_users():

    user = await db.fetch_user()

    return user
```

Execution begins.

```
HTTP Request

↓

Coroutine Created

↓

Task Created

↓

Event Loop Starts Executing
```

The coroutine runs until it reaches

```python
await db.fetch_user()
```

At this point,

```
Coroutine

↓

Pause

↓

Return Control

↓

Event Loop
```

The database query is now running.

Instead of waiting,

the event loop immediately switches to another ready coroutine.

---

## Complete Request Lifecycle

```
                HTTP Request

                      │

                      ▼

              Uvicorn Receives Request

                      │

                      ▼

             Coroutine Created

                      │

                      ▼

           Task Scheduled On Event Loop

                      │

                      ▼

          Execute Until await

                      │

                      ▼

        Coroutine Suspended

                      │

                      ▼

      Database / Redis / HTTP Request

                      │

                      ▼

          Operating System Waits

                      │

                      ▼

      I/O Operation Completes

                      │

                      ▼

   Operating System Notifies Event Loop

                      │

                      ▼

       Event Loop Resumes Coroutine

                      │

                      ▼

          Return HTTP Response
```

Notice something important.

The thread never waits.

Only the coroutine waits.

---

# The Operating System's Role

The event loop is not continuously checking,

> "Has PostgreSQL replied?"

That would waste CPU time.

Instead,

the operating system provides efficient notification mechanisms.

Examples include:

- **epoll** (Linux)
- **kqueue** (macOS, BSD)
- **IOCP** (Windows)

The sequence is:

```
Coroutine

↓

Starts Database Query

↓

Event Loop Registers Interest

↓

Operating System Waits

↓

Database Responds

↓

Operating System Notifies Event Loop

↓

Coroutine Resumes
```

The event loop wakes only the coroutines that are ready.

---

## Multiple Requests

Suppose three requests arrive simultaneously.

```
Request A

↓

await PostgreSQL

↓

Waiting
```

```
Request B

↓

await Redis

↓

Waiting
```

```
Request C

↓

CPU Work

↓

Running
```

The event loop behaves like this.

```
Time ------------------------------------------------>

Request A

Running

↓

Waiting

↓

Running Again

↓

Finished



Request B

Running

↓

Waiting

↓

Running Again

↓

Finished



Request C

Running

↓

Finished
```

Even though only one thread exists,

the CPU remains busy because the event loop continuously schedules whichever coroutine is ready.

---

# What Happens If We Call Blocking Code?

Consider

```python
@app.get("/")
async def users():

    data = requests.get("https://example.com")

    return data.text
```

`requests.get()` is synchronous.

It blocks the current thread.

Now,

the event loop cannot schedule any other coroutine.

```
Event Loop

↓

requests.get()

↓

Blocked
```

Every other request must wait.

This defeats the purpose of AsyncIO.

---

## Correct Approach

Use asynchronous libraries.

Instead of

```python
requests.get()
```

use

```python
await httpx.AsyncClient().get(...)
```

Instead of

```python
psycopg2
```

use

```python
asyncpg
```

Instead of

```python
redis-py (blocking)
```

use an asynchronous Redis client.

The rule is simple.

> If you're inside an async function, prefer async libraries whenever possible.

---

# What If We Must Call Blocking Code?

Sometimes,

a legacy library has no asynchronous API.

In that case,

run the blocking code in a thread pool.

Conceptually,

```
Coroutine

↓

Blocking Function

↓

Thread Pool

↓

Background Thread

↓

Result

↓

Coroutine Continues
```

This keeps the event loop free to handle other requests.

---

# Choosing the Right Concurrency Model

```
                    New Problem

                         │

                 CPU-bound?

               ┌─────────┴─────────┐

              Yes                 No

               │

      Multiprocessing

               │

               ▼

          Multiple Cores



----------------------------------------------



                 I/O-bound?

               ┌─────────┴─────────┐

              Yes                 No

               │

      Async Library Available?

          ┌────────┴─────────┐

         Yes                No

          │                  │

       AsyncIO        Multithreading
```

---

# Complete Mental Model

Everything we've learned can now be connected.

```
                HTTP Request

                      │

                      ▼

                 Uvicorn

                      │

                      ▼

                 Event Loop

                      │

             Creates Task

                      │

                      ▼

                Coroutine

                      │

               Executes Python

                      │

                 await I/O

                      │

             Coroutine Pauses

                      │

          Event Loop Runs Others

                      │

          Operating System Signals

                      │

             Coroutine Resumes

                      │

                 HTTP Response
```

---

## AsyncIO vs Multithreading vs Multiprocessing

| Feature | AsyncIO | Multithreading | Multiprocessing |
|----------|----------|----------------|-----------------|
| Concurrency | ✅ | ✅ | ✅ |
| Parallelism | ❌ | ❌ (CPython) | ✅ |
| Multiple Threads | ❌ | ✅ | Optional |
| Multiple Processes | ❌ | ❌ | ✅ |
| Event Loop | ✅ | ❌ | ❌ |
| Shared Memory | ✅ | ✅ | ❌ |
| Best For | Massive I/O | Blocking I/O | CPU-bound |
| Context Switch Cost | Very Low | Medium | High |

---

## Common Interview Questions

### What is AsyncIO?

AsyncIO is Python's asynchronous programming framework that enables a single thread to handle many concurrent I/O-bound operations using an event loop and coroutines.

---

### How does FastAPI handle thousands of requests?

Each request is represented as a coroutine.

The event loop schedules these coroutines and switches between them whenever one performs an `await`, allowing a single thread to efficiently manage many concurrent requests.

---

### Does AsyncIO bypass the GIL?

No.

Everything still runs inside one Python process and one GIL.

AsyncIO improves concurrency by avoiding blocking, not by achieving parallel execution.

---

### Does AsyncIO create threads?

No.

AsyncIO uses coroutines.

Threads are created only when explicitly required, such as running blocking code in a thread pool.

---

### Can AsyncIO improve CPU-bound code?

No.

CPU-bound workloads should use multiprocessing because AsyncIO cannot execute Python bytecode in parallel.

---

### Why is AsyncIO faster than creating thousands of threads?

Coroutines are lightweight and are scheduled by the event loop in user space, avoiding the memory overhead and operating system context switches associated with thousands of threads.

---

## Common Interview Mistakes

❌ Thinking `async` automatically makes code faster.

✔ AsyncIO improves throughput for I/O-bound workloads.

---

❌ Calling blocking libraries inside async functions.

✔ Prefer asynchronous libraries or run blocking code in a thread pool.

---

❌ Thinking AsyncIO replaces multiprocessing.

✔ AsyncIO is for concurrency, not CPU parallelism.

---

❌ Thinking `await` creates another thread.

✔ `await` simply suspends the current coroutine and returns control to the event loop.

---

## Interview Tip

If asked,

> **"How does FastAPI handle thousands of concurrent requests?"**

A strong answer is:

> "FastAPI is built on top of AsyncIO and runs on an event loop provided by an ASGI server such as Uvicorn. Each incoming request is represented as a coroutine. The event loop executes a coroutine until it reaches an `await`, at which point the coroutine is suspended and control returns to the event loop. While that coroutine waits for I/O, the event loop schedules another ready coroutine. When the operating system signals that the I/O operation has completed, the event loop resumes the suspended coroutine. This allows a single thread to efficiently handle thousands of concurrent I/O-bound requests."

---

## Key Takeaways

- AsyncIO is designed for high-concurrency I/O-bound applications.
- The event loop schedules and manages coroutine execution.
- Coroutines voluntarily suspend at `await` points.
- The operating system notifies the event loop when I/O is ready.
- FastAPI uses AsyncIO to handle many concurrent requests with a small number of threads.
- Use asynchronous libraries whenever possible inside async functions.
- Use a thread pool for unavoidable blocking operations.
- Use multiprocessing for CPU-bound workloads.
