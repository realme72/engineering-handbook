# How Does a Python Program Execute?

## Answer

When you run `python hello.py`, CPython doesn't execute your source text
directly. It first **compiles the source into bytecode**, and then a
**virtual machine interprets that bytecode**. So the source code is never
"run" in the literal sense — by the time anything actually executes, it's
been through a full compilation pipeline.

The flow is:

```
Source Code
    ↓
Tokenization       (source → tokens, so the parser has something structured to work with)
    ↓
Parsing            (tokens → AST, validates grammar)
    ↓
Compilation        (AST → bytecode, resolves scoping: local vs global vs closure)
    ↓
Bytecode           (cached in __pycache__ for imported modules)
    ↓
Python Virtual Machine   (stack-based interpreter, executes bytecode inside a frame)
    ↓
Output
```

---

## Explanation

### Step 1. Tokenization

The tokenizer reads the raw source text and breaks it into tokens — the
smallest meaningful units like `NAME`, `OP`, `STRING`, `NEWLINE`. The reason
this stage exists at all is that the **parser can't work directly on
characters** — it needs a clean, classified stream to match against
Python's grammar rules. So the tokens aren't just an abstract intermediate
step, they're literally the input alphabet the parser consumes next, one
token at a time.

One detail worth mentioning here: Python's grammar is
indentation-sensitive, but the parser itself doesn't reason about
whitespace — the tokenizer converts indentation changes into explicit
`INDENT` / `DEDENT` tokens up front, so by the time the parser sees the
stream, block structure looks just like it would in a brace-delimited
language.

```python
print("Hello")
```

tokenizes to roughly:

```
NAME(print)  OP(  STRING("Hello")  OP)  NEWLINE
```

### Step 2. Parsing

The parser consumes that token stream and checks it against Python's
grammar. If something doesn't fit — a missing colon, unbalanced
parentheses — this is where `SyntaxError` is raised. If it matches, the
parser builds an **Abstract Syntax Tree (AST)**: a tree that represents the
actual structure of the program rather than a flat sequence of tokens.

```python
print("Hello")
```

becomes, roughly:

```
Module
 └── Expr
      └── Call
           ├── func = Name("print")
           └── args = [Constant("Hello")]
```

The reason the parser bothers building a tree instead of handing tokens
straight to a compiler is that a tree captures *relationships* — which
expression is nested inside which call, which block belongs to which `if`
— and that structure is what every later stage (compiler, linters, static
analysis tools) actually needs.

### Step 3. Compilation to Bytecode

The compiler walks the AST and emits **bytecode** — a flat, linear
instruction sequence for CPython's virtual machine. Before it can do that,
it also builds a symbol table, because it needs to decide, per name,
whether it's a local variable, a global, or a closure variable — that
decision is what determines whether a name lookup compiles to a fast
array-index (`LOAD_FAST`) or a dictionary lookup (`LOAD_GLOBAL`).

```
LOAD_GLOBAL print
LOAD_CONST  "Hello"
CALL
POP_TOP
```

Bytecode is platform-independent — the same bytecode format runs on Linux,
macOS, or Windows for a given Python version — which is part of why Python
compiles to this intermediate form instead of straight to machine code.

### Step 4. Bytecode Caching

For imported modules, CPython writes this compiled bytecode to a `.pyc`
file inside `__pycache__`, so it doesn't have to re-parse and recompile the
same source on every run. It's invalidated automatically if the source file
changes (by comparing timestamp and size, or a hash of the source,
depending on the invalidation mode). One thing that trips people up: this
only applies to *imported* modules — the entry-point script you run
directly is always recompiled fresh.

### Step 5. The Python Virtual Machine (PVM)

The PVM is a stack-based interpreter — it executes bytecode instructions
one at a time, pushing and popping values off a per-frame value stack. Each
function call creates a new **frame**, which bundles the code object with
its own locals and its own stack, and the interpreter loop recurses into
it. This loop is also where the GIL comes in — only one thread executes
bytecode at a time, which is the actual mechanical reason pure-Python
threads don't give CPU parallelism.

### Step 6. Producing the Output

When the interpreter reaches the instructions for `print("Hello")`, it
calls the built-in `print`, which writes to `sys.stdout`, and the terminal
displays it.

---

## Diagram

```
                 python hello.py
                        │
                        ▼
            Python Interpreter (CPython)
                        │
                        ▼
          Lexical Analysis (Tokenization)
                        │
                        ▼
                    Parsing
                        │
                        ▼
          Abstract Syntax Tree (AST)
                        │
                        ▼
         Compilation to Python Bytecode
                        │
          ┌─────────────┴─────────────┐
          │                           │
          ▼                           ▼
     __pycache__ (.pyc)         Python Virtual Machine
                                          │
                                          ▼
                                 Execute Bytecode
                                          │
                                          ▼
                                        stdout
                                          │
                                          ▼
                                  Terminal Output
```

---

## Example

```python
print("Hello World")
```

```
Source Code → Tokens → AST → Bytecode → PVM → stdout → Hello World
```

---

## Follow-up Questions

### Is Python compiled or interpreted?

Both — the source is compiled to bytecode first, and that bytecode is what
gets interpreted. Calling it just "an interpreted language" undersells the
compilation step that happens before anything runs.

### Why compile to bytecode instead of walking the AST directly?

A tree has to be re-traversed and re-dispatched on every node every time
it's evaluated, which is expensive in a loop. A flat instruction array with
an instruction pointer is much cheaper to execute repeatedly, and it's also
what makes caching to `.pyc` possible in the first place.

### Why not compile straight to machine code?

Portability. Bytecode is the same across operating systems for a given
Python version, so the interpreter doesn't need a separate code generator
per platform. The tradeoff is you're paying interpretation overhead instead
of running native instructions directly — which is the gap PyPy's JIT
closes differently.

### Where are `.pyc` files stored, and does that apply to every script?

Inside `__pycache__`, and only for imported modules — the script you invoke
directly is recompiled every run.

---

## Key Takeaways

- Python source is compiled to bytecode before anything executes — it's not run as text.
- Tokenizing exists to give the parser a structured input; tokens feed directly into grammar matching.
- Parsing produces an AST because later stages need structure, not just a flat token list.
- The compiler resolves scoping (local/global/closure) while generating bytecode, which is why some name lookups are faster than others.
- `.pyc` caching only applies to imported modules, not the entry-point script.
- The PVM is a stack-based interpreter that executes bytecode inside per-call frames, and it's also where the GIL is enforced.
