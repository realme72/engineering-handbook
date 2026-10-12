# Multithreading

## What is Multithreading?

Multithreading is a **concurrency model** in which a single process creates multiple threads of execution. These threads share the same address space and process resources while independently executing different parts of a program.

Since threads share memory, communication between them is inexpensive compared to processes, making multithreading well suited for I/O-bound applications such as web servers, database operations, and network communication.

> **Note:** In CPython, although multiple threads exist within a process, only one thread executes Python bytecode at a time because of the Global Interpreter Lock (GIL). Refer to the **GIL** chapter for a detailed explanation.

---

## What is a Thread?

A thread is the **smallest unit of execution** scheduled by the operating system within a process.

Each thread has its own:

- Stack
- Program Counter
- CPU Registers

All threads within the same process share:

- Heap Memory
- Global Variables
- Open Files
- Process Resources

---

## Thread Architecture

```
                 Process

    +-----------------------------------+
    |           Shared Heap             |
    |        Global Variables           |
    |          Open Files               |
    +-----------------------------------+

         ▲                ▲
         │                │

     Thread 1         Thread 2

     Stack            Stack
     Registers        Registers
     Program Counter  Program Counter
```

---

## Why Does Every Thread Have Its Own Stack?

Consider

```python
def foo():
    x = 10
```

Suppose two threads execute this function simultaneously.

Thread 1

```python
x = 10
```

Thread 2

```python
x = 20
```

Each thread maintains its own call stack.

```
Thread 1

Stack

foo()
x = 10
```

```
Thread 2

Stack

foo()
x = 20
```

This prevents local variables from interfering with one another.

---

## Creating a Thread

Python provides the `threading` module.

```python
from threading import Thread

def worker():
    print("Working...")

thread = Thread(target=worker)

thread.start()
```

Output

```
Working...
```

---

## Passing Arguments

```python
from threading import Thread

def greet(name):
    print(f"Hello {name}")

thread = Thread(target=greet, args=("Gaurav",))

thread.start()
```

Output

```
Hello Gaurav
```

---

## start() vs run()

A common interview question.

```python
thread.start()
```

Creates a **new operating system thread**.

```
Main Thread

↓

start()

↓

New Thread Created

↓

run()

↓

Target Function Executes
```

---

```python
thread.run()
```

Does **not** create a new thread.

It simply executes the function in the current thread.

```
Current Thread

↓

run()

↓

Target Function Executes
```

Always use `start()` to create a new thread.

---

## Waiting for Threads

```python
from threading import Thread

def worker():
    print("Working")

thread = Thread(target=worker)

thread.start()

thread.join()

print("Finished")
```

Output

```
Working
Finished
```

`join()` blocks the calling thread until the target thread completes.

---

## Thread Lifecycle

```
New
 │
 ▼
Runnable
 │
 ▼
Running
 │
 ▼
Blocked / Waiting
 │
 ▼
Running
 │
 ▼
Terminated
```

A thread may enter the blocked state while waiting for:

- Network I/O
- Database Queries
- File I/O
- Locks
- Sleep

---

## Creating Multiple Threads

```python
from threading import Thread

def worker(i):
    print(f"Worker {i}")

threads = []

for i in range(5):
    thread = Thread(target=worker, args=(i,))
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()
```

Execution order is **not guaranteed** because thread scheduling is handled by the operating system.

---

## Daemon Threads

By default, Python waits for all threads to finish before exiting.

A daemon thread runs in the background and automatically terminates when the main program exits.

```python
from threading import Thread
import time

def monitor():
    while True:
        print("Monitoring...")
        time.sleep(1)

thread = Thread(target=monitor, daemon=True)

thread.start()
```

Typical use cases:

- Logging
- Monitoring
- Metrics Collection
- Background Cleanup

---

## ThreadPoolExecutor

Creating threads repeatedly is expensive.

Instead, use a thread pool.

```python
from concurrent.futures import ThreadPoolExecutor

def square(x):
    return x * x

with ThreadPoolExecutor(max_workers=4) as executor:

    results = executor.map(square, [1, 2, 3, 4])

print(list(results))
```

Output

```
[1, 4, 9, 16]
```

The thread pool creates a fixed number of worker threads and reuses them.

---

## Futures

Submitting a task returns a `Future`.

```python
from concurrent.futures import ThreadPoolExecutor

def square(x):
    return x * x

with ThreadPoolExecutor() as executor:

    future = executor.submit(square, 10)

print(future.result())
```

Output

```
100
```

A `Future` represents the result of a computation that may complete later.

---

## Thread Communication

Threads share the same memory.

```python
counter = 0
```

While sharing memory is efficient, it also introduces race conditions.

Shared mutable state should be protected using synchronization primitives such as:

- Lock
- RLock
- Semaphore
- Event
- Condition

These are covered in the **Synchronization** chapter.

---

## Real-World Examples

### Downloading Multiple Files

```
Thread 1

↓

Download File A
```

```
Thread 2

↓

Download File B
```

```
Thread 3

↓

Download File C
```

---

### Calling Multiple APIs

```
Thread 1

↓

Payment API
```

```
Thread 2

↓

Notification API
```

```
Thread 3

↓

Inventory API
```

---

### Background Logging

```
Main Thread

↓

Handle Request

↓

Return Response


Background Thread

↓

Write Logs
```

---

## Common Interview Questions

### What is multithreading?

Multithreading is a concurrency model in which multiple threads execute within the same process while sharing the same address space and process resources.

---

### Why are threads lightweight?

Threads share the same memory and process resources.

Only a new stack, program counter, and register set are allocated.

---

### What resources are shared?

- Heap Memory
- Global Variables
- Open Files
- Process Resources

---

### What resources are private?

- Stack
- Registers
- Program Counter

---

### Difference between `start()` and `run()`?

`start()`

Creates a new thread.

`run()`

Executes in the current thread.

---

### What is `join()`?

`join()` blocks the calling thread until the target thread finishes.

---

### What is a daemon thread?

A background thread that automatically terminates when the main program exits.

---

### What is ThreadPoolExecutor?

A high-level API that manages and reuses a pool of worker threads.

---

### What is a Future?

A placeholder representing the result of a task that may complete asynchronously.

---

## Common Interview Mistakes

❌ Calling `run()` instead of `start()`.

✔ Always use `start()` to create a new thread.

---

❌ Assuming thread execution order is deterministic.

✔ Thread scheduling is controlled by the operating system.

---

❌ Creating hundreds of threads manually.

✔ Prefer `ThreadPoolExecutor`.

---

❌ Accessing shared mutable state without synchronization.

✔ Use locks and other synchronization primitives.

---

## Interview Tip

If asked:

> **When would you use multithreading?**

A strong answer is:

> "I use multithreading for I/O-bound workloads such as database operations, REST API calls, file processing, logging, and background tasks. Since threads share memory, they're lightweight and efficient for workloads where most of the execution time is spent waiting for external resources."

---

## Key Takeaways

- Multithreading enables multiple threads to execute within the same process.
- Threads share memory and process resources.
- Each thread has its own stack, registers, and program counter.
- Use `start()` to create a new thread.
- Use `join()` to wait for completion.
- Daemon threads are suitable for background tasks.
- `ThreadPoolExecutor` is preferred for managing multiple worker threads.
- Multithreading is best suited for I/O-bound workloads.