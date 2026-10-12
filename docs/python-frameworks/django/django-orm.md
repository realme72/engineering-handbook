# Django ORM Interview Handbook

> This handbook is not meant to teach Django ORM from scratch.
>
> It's meant to teach you how experienced backend engineers think about the ORM during interviews.
>
> Every answer is written from the perspective of someone who has designed, built, optimized, and debugged production Django applications.
>
> The focus isn't on memorizing QuerySet APIs.
>
> The focus is understanding how the ORM works, what SQL it generates, and how to use it efficiently in production.

---

# Prerequisites

Before reading this handbook, you should understand:

- Python
- OOP
- SQL
- Relational Databases
- Basic Django Models

---

# How To Use This Handbook

Every interview answer follows the same philosophy.

```
Problem

↓

Why does this exist?

↓

How Django ORM solves it

↓

Production Perspective

↓

Trade-offs

↓

Possible Follow-up Questions
```

If you understand the problem,

the API becomes easy to remember.

---

# Table of Contents

## Foundations

1. What is an ORM?
2. Why does ORM exist?
3. How Django ORM works internally
4. ORM vs Raw SQL

## QuerySets

5. What is a QuerySet?
6. Why is QuerySet Lazy?
7. When does a QuerySet execute?
8. QuerySet Cache

## Querying

9. filter() vs exclude()
10. get()
11. first() & last()
12. exists()
13. values()
14. values_list()
15. only()
16. defer()

## Relationships

17. select_related()
18. prefetch_related()
19. select_related vs prefetch_related

## Advanced Querying

20. annotate()
21. aggregate()
22. F Expressions
23. Q Objects
24. Subquery
25. Exists

## Performance

26. N+1 Queries
27. bulk_create()
28. bulk_update()
29. iterator()
30. explain()
31. Raw SQL

## Transactions

32. transaction.atomic()
33. select_for_update()

## Production

34. Common ORM Mistakes
35. Debugging Slow Queries
36. Production Incidents

---

# Question 1

## Interviewer

**What is an ORM?**

---

## Answer

The way I think about an ORM is,

it's a bridge between my application and the database.

Suppose I want to fetch a user.

Without an ORM,

I'd probably write something like

```sql
SELECT *
FROM users
WHERE id = 1;
```

I execute the query,

the database returns a row,

and then I manually convert that row into a Python object.

So every time I interact with the database,

I'm constantly switching between two worlds.

One world understands Python objects.

The other understands SQL tables and rows.

What the ORM does is bridge those two worlds.

Instead of writing SQL directly,

I can simply write

```python
user = User.objects.get(id=1)
```

Under the hood,

Django generates the SQL,

executes it,

takes the result,

creates a `User` object,

and gives it back to me.

So I usually think of the ORM as a translator.

I write Python.

The database speaks SQL.

The ORM translates between the two.

One thing I always keep in mind though is that SQL never disappears.

Every QuerySet eventually becomes a SQL query.

That's why whenever I'm debugging performance,

I don't just look at the Python code.

I also inspect the SQL Django generated and the execution plan.

---

## Production Perspective

For most CRUD APIs,

I rely entirely on the ORM.

It keeps the code clean,

consistent,

and easy to maintain across the team.

But if I need complex reporting,

window functions,

recursive CTEs,

or highly optimized analytics queries,

I'm perfectly happy writing raw SQL.

I don't consider that bypassing the ORM.

I consider it using the right tool for the problem.

---

## Trade-offs

### Advantages

- Cleaner code
- Database abstraction
- Safer queries
- Easier relationships
- Built-in transaction support
- Easier migrations

### Limitations

- Doesn't always generate optimal SQL
- Can hide expensive queries
- Some SQL features are awkward to express
- Easy to introduce performance issues without realizing it

---

## Follow-up Questions

- How does Django ORM actually generate SQL?
- What is a QuerySet?
- Why is QuerySet lazy?
- When does a QuerySet execute?
- When would you choose raw SQL?

---

# Question 2

## Interviewer

**Why does Django ORM exist? Why not just write SQL?**

---

## Answer

That's a fair question.

I actually don't think the ORM exists because writing SQL is difficult.

Most backend engineers should be comfortable writing SQL.

The real problem is repetition.

Imagine every API in a project needs to

- connect to the database
- write SQL
- execute the query
- fetch rows
- map rows into Python objects
- handle relationships
- escape parameters safely

Every developer ends up writing the same plumbing.

The ORM standardizes all of that.

Instead of everyone solving the same problem differently,

the team works with a common abstraction.

It also makes the code much more expressive.

When I see

```python
User.objects.filter(is_active=True)
```

I immediately understand the intent.

I don't have to mentally parse SQL first.

---

## Production Perspective

One of the biggest benefits I've seen is consistency.

Every developer on the team queries the database the same way.

That makes code reviews easier,

reduces bugs,

and makes onboarding much faster.

---

## Trade-offs

Using the ORM doesn't remove the need to understand SQL.

In fact,

I think using an ORM without understanding SQL is dangerous.

Whenever performance becomes important,

I always think about the SQL that's actually being executed underneath.

---

## Follow-up Questions

- How does the ORM convert Python into SQL?
- What happens internally when we call `User.objects.filter()`?
- What exactly is a QuerySet?

---

# Question 3

## Interviewer

**How does Django ORM work internally?**

---

## Answer

Suppose I write

```python
users = User.objects.filter(is_active=True)
```

At first,

nothing is sent to the database.

Django creates a QuerySet object.

Think of that QuerySet as a blueprint for the SQL that needs to be executed.

```
Python Code

↓

QuerySet

↓

SQL

↓

Database

↓

Rows

↓

Python Objects
```

As I keep chaining methods,

```python
users = (
    User.objects
        .filter(is_active=True)
        .exclude(is_staff=True)
        .order_by("-created_at")
)
```

Django keeps modifying that blueprint.

It still hasn't talked to the database.

Only when I actually need the data,

Django generates the SQL,

executes it,

converts the rows into model objects,

and returns the results.

That's one of the reasons QuerySets are lazy,

which is usually the next interview question.

---

## Production Perspective

Understanding this flow helps explain why certain operations unexpectedly hit the database.

If I know when a QuerySet gets evaluated,

it's much easier to debug performance issues and avoid unnecessary queries.

---

## Follow-up Questions

- What is a QuerySet?
- Why is QuerySet lazy?
- When is SQL actually generated?
- What triggers evaluation?