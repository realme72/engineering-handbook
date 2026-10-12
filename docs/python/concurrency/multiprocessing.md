# Multiprocessing

## What is Multiprocessing?

Multiprocessing is a **parallel execution model** in which a program creates multiple independent processes to execute tasks simultaneously.

Unlike threads, each process has its own:

- Python Interpreter
- Memory Space
- Global Interpreter Lock (GIL)

Since processes do not share the same interpreter, they can execute Python bytecode in parallel across multiple CPU cores.

Multiprocessing is the preferred choice for **CPU-bound workloads**.

---

## Process Architecture

```
                  CPU

        ┌────────┼────────┬────────┐
        ▼        ▼        ▼        ▼

    Process 1 Process 2 Process 3 Process 4

       GIL       GIL       GIL       GIL

      Heap      Heap      Heap      Heap

     Thread    Thread    Thread    Thread
```

Each process is completely independent.

---

## Process vs Thread

```
Threads

One Process

      Shared Heap

   ┌─────┼─────┐

Thread Thread Thread

Shared Memory
Shared GIL
```

```
Processes

Process 1      Process 2      Process 3

Heap           Heap           Heap

GIL            GIL            GIL
```

---

## Why Use Multiprocessing?

Suppose we have

```python
def calculate():

    total = 0

    for i in range(1_000_000_000):
        total += i
```

Running this using multiple threads will not improve performance because all threads compete for the same GIL.

Instead,

creating multiple processes allows each process to execute on a different CPU core.

```
Core 1

Process 1


Core 2

Process 2


Core 3

Process 3


Core 4

Process 4
```

Now all computations execute simultaneously.

---

## Creating a Process

Python provides the `multiprocessing` module.

```python
from multiprocessing import Process

def worker():
    print("Working...")

process = Process(target=worker)

process.start()

process.join()
```

Output

```
Working...
```

---

## Passing Arguments

```python
from multiprocessing import Process

def square(x):
    print(x * x)

process = Process(target=square, args=(10,))

process.start()

process.join()
```

Output

```
100
```

---

## start() vs join()

```python
process.start()
```

Creates a new operating system process.

```python
process.join()
```

Waits until the process completes.

---

## Creating Multiple Processes

```python
from multiprocessing import Process

def worker(i):
    print(f"Process {i}")

processes = []

for i in range(4):

    process = Process(target=worker, args=(i,))

    process.start()

    processes.append(process)

for process in processes:
    process.join()
```

---

## Process Pool

Creating processes repeatedly is expensive.

Python provides a process pool.

```python
from multiprocessing import Pool

def square(x):
    return x * x

with Pool(processes=4) as pool:

    result = pool.map(square, [1,2,3,4])

print(result)
```

Output

```
[1,4,9,16]
```

Worker processes are reused.

---

## ProcessPoolExecutor

A higher-level API.

```python
from concurrent.futures import ProcessPoolExecutor

def square(x):
    return x * x

with ProcessPoolExecutor() as executor:

    result = executor.map(square,[1,2,3,4])

print(list(result))
```

---

## Inter-Process Communication (IPC)

Processes do **not** share memory.

Therefore,

they must communicate explicitly.

Python provides several IPC mechanisms.

- Queue
- Pipe
- Shared Memory
- Manager

---

## Queue

A Queue allows processes to safely exchange data.

```python
from multiprocessing import Process, Queue

def worker(queue):

    queue.put("Hello")

queue = Queue()

process = Process(target=worker, args=(queue,))

process.start()

print(queue.get())

process.join()
```

Output

```
Hello
```

---

## Pipe

A Pipe provides direct communication between two processes.

```python
from multiprocessing import Process, Pipe

def worker(conn):

    conn.send("Hello")

parent, child = Pipe()

process = Process(target=worker, args=(child,))

process.start()

print(parent.recv())

process.join()
```

Output

```
Hello
```

---

## Shared Memory

Normally,

each process has its own memory.

Sometimes data must be shared.

Python provides

```python
multiprocessing.shared_memory
```

for sharing memory between processes.

---

## Manager

A Manager allows multiple processes to share Python objects.

```python
from multiprocessing import Manager

manager = Manager()

shared_list = manager.list()

shared_list.append(1)
```

Supported shared objects include:

- list
- dict
- Namespace
- Lock
- Queue

---

## Real-World Examples

### Image Processing

```
Core 1

Resize Image 1
```

```
Core 2

Resize Image 2
```

```
Core 3

Resize Image 3
```

---

### Machine Learning

```
Process 1

Train Batch 1
```

```
Process 2

Train Batch 2
```

---

### Data Processing

```
CSV File

↓

Split

↓

Process 1

↓

Process 2

↓

Process 3

↓

Merge Results
```

---

### Video Encoding

Each process encodes different frames simultaneously.

---

## Common Interview Questions

### What is multiprocessing?

Multiprocessing is a parallel execution model where multiple independent processes execute simultaneously.

---

### Why does multiprocessing bypass the GIL?

Each process has its own Python interpreter and its own GIL.

---

### Do processes share memory?

No.

Each process has an independent memory space.

---

### How do processes communicate?

Using IPC mechanisms such as:

- Queue
- Pipe
- Shared Memory
- Manager

---

### Difference between Pool and Process?

`Process`

Manually create processes.

`Pool`

Automatically manages a pool of reusable worker processes.

---

### What is ProcessPoolExecutor?

A high-level API for managing worker processes.

---

## Common Interview Mistakes

❌ Thinking multiprocessing shares memory.

✔ Every process has its own address space.

---

❌ Using multiprocessing for I/O-bound work.

✔ Use multiprocessing primarily for CPU-bound workloads.

---

❌ Creating too many processes.

✔ Usually create at most one process per CPU core.

---

## Interview Tip

If asked:

> **When would you use multiprocessing?**

A strong answer is:

> "I use multiprocessing for CPU-intensive workloads such as image processing, video encoding, data processing, machine learning, and large mathematical computations. Since each process has its own interpreter and GIL, multiprocessing achieves true parallelism across multiple CPU cores."

---

## Key Takeaways

- Multiprocessing creates multiple independent processes.
- Every process has its own interpreter, memory, and GIL.
- Multiprocessing provides true parallel execution.
- Processes communicate using IPC mechanisms.
- Use `Pool` or `ProcessPoolExecutor` instead of creating processes manually.
- Multiprocessing is best suited for CPU-bound workloads.