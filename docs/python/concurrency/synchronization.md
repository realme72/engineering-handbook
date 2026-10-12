# Synchronization

## Why Do We Need Synchronization?

Multiple threads or processes often access the same shared resource.

Without synchronization, concurrent access can produce inconsistent or incorrect results.

Suppose two threads increment the same variable.

```python
counter = 0
```

Both execute

```python
counter += 1
```

This looks like a single operation, but it actually consists of three steps.

```
Read Counter

↓

Increment

↓

Write Counter
```

Now imagine two threads executing simultaneously.

```
Counter = 0


Thread 1

Read 0


Thread 2

Read 0


Thread 1

Write 1


Thread 2

Write 1
```

Expected result

```
Counter = 2
```

Actual result

```
Counter = 1
```

One update is lost.

This is called a **race condition**.

---

## Race Condition

A **race condition** occurs when multiple threads or processes access and modify shared mutable data concurrently, causing unpredictable results.

Race conditions usually occur because operations that appear atomic are actually composed of multiple steps.

Examples include:

- Bank balance updates
- Inventory management
- Counters
- Shared caches
- Shared files

---

## Critical Section

A **critical section** is a portion of code that accesses shared mutable resources and therefore must not be executed simultaneously by multiple threads or processes.

Example

```python
counter += 1
```

Conceptually,

```
Critical Section

Read Counter

↓

Modify Counter

↓

Write Counter
```

Only one thread should execute this code at a time.

Synchronization primitives protect critical sections.

---

# Lock

A **Lock** ensures that only one thread can enter a critical section at a time.

```
Thread 1

Acquire Lock

↓

Critical Section

↓

Release Lock
```

Meanwhile,

```
Thread 2

Waiting...
```

Example

```python
from threading import Lock

counter = 0

lock = Lock()

def increment():

    global counter

    with lock:

        counter += 1
```

The `with` statement automatically acquires and releases the lock.

---

## Lock Visualization

```
               Lock

                │

Thread 1 ───────┘

Executing Critical Section


Thread 2

Waiting


Thread 3

Waiting
```

Once Thread 1 releases the lock,

another waiting thread acquires it.

---

# RLock (Reentrant Lock)

A **Reentrant Lock** allows the same thread to acquire the same lock multiple times.

Suppose

```python
def foo():

    with lock:

        bar()

def bar():

    with lock:

        ...
```

Using a normal Lock,

```
foo()

↓

Acquire Lock

↓

bar()

↓

Acquire Lock Again

↓

Deadlock
```

The thread waits for a lock it already owns.

An RLock avoids this.

```
Thread

Acquire

↓

Acquire Again

↓

Acquire Again

↓

Release

↓

Release

↓

Release
```

Example

```python
from threading import RLock

lock = RLock()
```

---

# Semaphore

A Lock allows

```
1 Thread
```

A Semaphore allows

```
N Threads
```

Suppose

```python
Semaphore(3)
```

Conceptually,

```
Available Slots = 3

Thread 1

Enter

Slots = 2


Thread 2

Enter

Slots = 1


Thread 3

Enter

Slots = 0


Thread 4

Waiting...
```

Common use cases:

- Database connection pools
- Limiting concurrent downloads
- Rate limiting

Example

```python
from threading import Semaphore

semaphore = Semaphore(3)
```

---

# Event

An Event is used for signaling between threads.

One thread waits.

Another thread notifies.

```
Thread 1

event.wait()

↓

Waiting...
```

```
Thread 2

event.set()
```

Thread 1 immediately resumes.

Example

```python
from threading import Event

event = Event()

event.wait()

event.set()
```

Common use cases:

- Startup synchronization
- Worker coordination
- Background services

---

# Condition

A Condition allows threads to wait until a particular condition becomes true.

Producer

```
Produce Item

↓

Notify
```

Consumer

```
Wait

↓

Consume Item
```

Example

```python
from threading import Condition

condition = Condition()
```

Typical use cases:

- Producer / Consumer
- Task queues
- Resource availability

---

# Deadlock

A deadlock occurs when two or more threads wait indefinitely for resources held by each other.

Example

```
Thread 1

Lock A

↓

Waiting for Lock B
```

```
Thread 2

Lock B

↓

Waiting for Lock A
```

Neither thread can continue.

```
Thread 1 ◄────────► Thread 2
```

This situation is called a deadlock.

---

## Avoiding Deadlocks

- Always acquire locks in the same order.
- Keep critical sections small.
- Avoid nested locks whenever possible.
- Use timeouts when appropriate.

---

# Choosing the Right Primitive

```
Need exclusive access?

↓

Lock



Need recursive locking?

↓

RLock



Allow N threads?

↓

Semaphore



Need thread signaling?

↓

Event



Need to wait for a condition?

↓

Condition
```

---

# Real-World Examples

## Updating Account Balance

```
Thread

↓

Acquire Lock

↓

Update Balance

↓

Release Lock
```

---

## Database Connection Pool

```
Pool Size = 10

↓

Semaphore(10)
```

---

## Producer / Consumer

```
Producer

↓

Queue

↓

Consumer

Condition Variable
```

---

## Application Startup

```
Thread 1

Load Configuration

↓

event.set()
```

```
Thread 2

event.wait()

↓

Continue Startup
```

---

# Common Interview Questions

### What is synchronization?

Synchronization is the process of coordinating multiple threads or processes so they can safely access shared resources.

---

### What is a race condition?

A race condition occurs when concurrent access to shared mutable data produces unpredictable results.

---

### What is a critical section?

A portion of code that accesses shared mutable resources and must not be executed concurrently.

---

### Difference between Lock and RLock?

Lock can be acquired only once.

RLock allows the same thread to acquire the lock multiple times.

---

### When would you use a Semaphore?

When a limited number of threads should access a shared resource simultaneously.

---

### When would you use an Event?

To signal one or more waiting threads that an event has occurred.

---

### When would you use a Condition?

When threads must wait until a specific condition becomes true.

---

### What is a deadlock?

A situation where two or more threads wait indefinitely for resources held by each other.

---

# Common Interview Mistakes

❌ Assuming the GIL removes the need for synchronization.

✔ The GIL protects Python's internal memory management, not your application's shared data.

---

❌ Using Lock everywhere.

✔ Choose the synchronization primitive based on the problem.

---

❌ Holding locks for a long time.

✔ Keep critical sections as short as possible.

---

❌ Acquiring locks in different orders.

✔ Always maintain a consistent locking order.

---

# Interview Tip

If asked,

> "When do you need synchronization?"

A strong answer is:

> "Whenever multiple threads or processes access shared mutable resources. Synchronization prevents race conditions by ensuring only the intended number of execution units can enter a critical section at a time."

---

# Key Takeaways

- Synchronization protects shared mutable resources.
- Race conditions occur due to concurrent access to shared state.
- A critical section is code that must execute exclusively.
- Lock provides mutual exclusion.
- RLock allows recursive locking.
- Semaphore limits concurrent access.
- Event enables thread signaling.
- Condition coordinates threads based on state changes.
- Proper synchronization prevents race conditions and deadlocks.