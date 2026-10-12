# Threads & Processes — Fundamentals

## Process — the fundamental unit of isolation

A **process** is an instance of a running program, and the OS gives it its own **isolated address space**. Concretely, when the OS creates a process it sets up:

- **Virtual memory space** — its own page tables, so process A can't see or touch process B's memory. Enforced by the MMU (memory management unit) in hardware.
- **Its own copy of code, data, heap, stack**
- **File descriptors / open handles**
- **Process Control Block (PCB)** — kernel-side bookkeeping: PID, register state, scheduling info, memory map pointers, open file table, etc.

Because processes are isolated, communication between them requires explicit **IPC** (inter-process communication) — pipes, sockets, shared memory segments, message queues. Nothing is shared by default.

Creating a process is relatively expensive: `fork()` (on Unix) duplicates the parent's address space (copy-on-write these days, so it's cheaper than it sounds, but still involves new page tables, new PCB, etc.), and `exec()` then loads a new program image into it.

## Thread — the fundamental unit of execution within a process

A **thread** is a sequence of instructions the CPU executes — it's what actually gets scheduled onto a CPU core. A process always has at least one thread (main thread), and can spawn more.

Key idea: **threads within the same process share the address space** — same heap, same global variables, same open file descriptors, same code segment. What each thread gets *privately* is:

- Its own **stack** (local variables, return addresses, function call frames)
- Its own **register set / program counter** — this is literally what defines "where execution currently is"
- Its own **thread ID** and scheduling state

That's it. Everything else — heap-allocated objects, globals, static data — is shared.

This has two big consequences:

1. **Thread creation/switching is cheap.** No new address space, no new page tables — just a new stack and register context. A **context switch** between threads in the same process just swaps register state and stack pointer; switching between processes also has to swap the memory mapping (page table base register), which is costlier — hence the general rule "threads are lighter than processes."

2. **Shared memory means race conditions.** Since threads see the same heap, two threads writing to the same variable concurrently is undefined/dangerous behavior unless you synchronize — hence mutexes, semaphores, condition variables, atomics. This is the entire reason concurrent programming is hard: isolation (process) is safe but expensive to communicate across; sharing (threads) is cheap to communicate but requires you to manually protect every shared mutation.

## The scheduler's view

The OS scheduler doesn't really schedule "processes" — it schedules **threads** (in Linux, both are represented internally as `task_struct`; a "process" is just a thread group with a shared address space). Each core runs one thread at a time (ignoring hyperthreading), and the scheduler time-slices between all runnable threads across all processes, using a scheduling algorithm (e.g., Linux's CFS — Completely Fair Scheduler) to decide who runs next based on priority/fairness.

On a **multi-core machine**, true parallelism happens: different cores run different threads simultaneously. On a single core, you get **concurrency** via time-slicing (rapid switching creates the illusion of simultaneity) but not true parallelism.

## Where Python complicates this

CPython has the **GIL (Global Interpreter Lock)** — only one thread can execute Python bytecode at a time, even on a multi-core machine. So:

- **Threading in Python** gives you concurrency, not parallelism, for CPU-bound work — useful for I/O-bound tasks (network calls, disk I/O) where a thread releases the GIL while waiting.
- **CPU-bound parallel work** in Python typically needs `multiprocessing` (separate processes, separate GILs, separate memory — communicate via pickling over pipes/queues) or dropping to C-extensions that release the GIL (numpy, etc.).
- This is exactly why Python microservices architectures often lean on **process-level parallelism** (multiple worker processes behind a load balancer, e.g. Gunicorn workers) rather than threading for CPU-bound throughput — sidesteps the GIL entirely, and you get the isolation as a bonus (one worker crashing doesn't take down others).

## Quick mental model to keep

| | Process | Thread |
|---|---|---|
| Memory | Isolated | Shared (except stack/registers) |
| Creation cost | Expensive | Cheap |
| Context switch cost | Expensive (page table swap) | Cheap |
| Communication | Explicit IPC | Direct (shared memory) — needs locking |
| Crash isolation | One process crashing doesn't affect others | One thread crashing (segfault) can take down the whole process |
| Failure mode of concurrency bugs | Deadlock over IPC resources | Race conditions, deadlocks over shared state |
