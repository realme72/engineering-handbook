# Pagination

## Prerequisites

Before reading this chapter, you should be familiar with:

- REST APIs
- HTTP Basics
- SQL (`SELECT`, `WHERE`, `ORDER BY`, `LIMIT`)
- Database Indexes (recommended)

---

# Why Do We Need Pagination?

Let's begin with a simple query.

```sql
SELECT
    order_id,
    created_at,
    updated_at,
    order_info
FROM orders
WHERE user_id = 'abc123';
```

Suppose this customer has placed only **5 orders**.

The query returns 5 rows and everything works perfectly.

Now imagine the same customer has been using your application for several years and has accumulated **15,000 orders**.

The query hasn't changed.

The amount of data has.

Now think from the user's perspective.

When the customer opens the **My Orders** page, do they actually see all 15,000 orders?

Of course not.

Almost every application displays only a small portion of the data at a time.

```
┌──────────────────────────────┐
│         My Orders            │
├──────────────────────────────┤
│ Order #15421                 │
│ Order #15420                 │
│ Order #15419                 │
│ ...                          │
│ Order #15402                 │
├──────────────────────────────┤
│ Previous            Next     │
└──────────────────────────────┘
```

Typically, the UI displays somewhere between **10 and 50 records** on a single screen.

Fetching all 15,000 rows just to display the first 20 is wasteful.

Every layer of the system performs unnecessary work.

- The database spends time producing thousands of rows.
- The application allocates memory to hold those rows.
- The response must be serialized into JSON (or another response format).
- Thousands of records are transferred over the network.
- The client receives data it never renders.

Most of this work provides no value because the user only looks at a tiny fraction of the dataset.

Instead, we retrieve only the rows required to render the current screen.

```http
GET /orders?limit=20
```

The server returns only the first 20 records.

When the user clicks **Next**, the application requests the next 20.

This technique of retrieving data in small chunks instead of loading the entire dataset is called **pagination**.

---

# Benefits of Pagination

Pagination provides several advantages:

- Reduces database work
- Reduces network bandwidth
- Keeps API response times predictable
- Reduces memory usage on both the server and client
- Improves user experience
- Makes APIs scalable as datasets continue to grow

---

# Types of Pagination

Most backend systems use one of the following pagination strategies:

1. Offset Pagination
2. Cursor (Keyset) Pagination
3. Token Pagination

We'll discuss each of them individually.

---

# Offset Pagination

Offset pagination is the simplest and most commonly used pagination strategy.

The client specifies two values:

- **limit** – maximum number of rows to return
- **offset** – number of rows to skip before returning results

Example request:

```http
GET /orders?limit=20&offset=40
```

The backend executes:

```sql
SELECT
    order_id,
    created_at,
    updated_at,
    order_info
FROM orders
WHERE user_id = 'abc123'
ORDER BY created_at DESC
LIMIT 20 OFFSET 40;
```

Here,

- `OFFSET 40` tells the database to skip the first 40 rows in the ordered result set.
- `LIMIT 20` tells it to return only the next 20 rows.

Conceptually,

```
Rows

1
2
3
...
40   ← skipped

41
42
43
...
60   ← returned
```

This makes implementing page-based navigation straightforward.

For example,

```
Page Size = 20

Page 1 → OFFSET 0
Page 2 → OFFSET 20
Page 3 → OFFSET 40
Page 4 → OFFSET 60
```

The offset can easily be calculated as:

```
OFFSET = (page_number - 1) × page_size
```

---

# Why Does OFFSET Become Slow?

One common misconception is that the database can directly jump to the requested offset.

For example,

```sql
LIMIT 20 OFFSET 1000000
```

does **not** mean

> Jump directly to row 1,000,001.

Instead, the database must advance through the first one million rows of the ordered result before it can begin returning results.

Conceptually,

```
Read row 1
Discard

Read row 2
Discard

...

Read row 1,000,000
Discard

Return next 20 rows
```

If an index exists, the database usually traverses the index rather than scanning the entire table, but it still needs to walk through the skipped entries.

As the offset grows, the amount of work also grows.

For small offsets, this overhead is negligible.

For very large offsets, it becomes increasingly expensive.

---

# Problems with Offset Pagination

## 1. Performance Degrades on Deep Pages

Suppose your table contains 50 million rows.

Requesting

```http
GET /orders?limit=20&offset=40000000
```

requires traversing approximately forty million ordered entries before returning just twenty rows.

The deeper the page, the slower the query becomes.

---

## 2. Unstable Under Concurrent Writes

Offset pagination assumes that the dataset remains unchanged between requests.

In production systems, this assumption rarely holds.

Imagine Page 1 returns

```
1
2
3
4
5
```

Before the user requests Page 2, another order is inserted at the beginning.

The dataset now becomes

```
0
1
2
3
4
5
6
7
...
```

The second request still asks for

```
OFFSET 5
```

The results now become

```
5
6
7
8
9
```

Notice that **5 appears twice**.

Similarly, if rows are deleted, some records may never appear in the paginated results.

This is one of the major limitations of offset pagination.

---

# Cursor (Keyset) Pagination

Cursor pagination approaches the problem differently.

Instead of asking

> Skip the first N rows

it asks

> Continue after this specific row.

Suppose the last row returned has

```
id = 100
```

The next request becomes

```http
GET /orders?limit=20&cursor=100
```

The backend executes

```sql
SELECT
    order_id,
    created_at,
    updated_at,
    order_info
FROM orders
WHERE id > 100
ORDER BY id
LIMIT 20;
```

The response contains

```json
{
    "data": [
        ...
    ],
    "next_cursor": 120
}
```

The client stores this cursor and sends it back when requesting the next page.

---

# Why Cursor Pagination Scales Better

Unlike offset pagination,

```sql
WHERE id > 100
```

allows the database to use the index to seek directly to the first matching row.

Instead of traversing one million previous rows,

the database jumps directly to

```
101
```

and begins reading from there.

The amount of work remains roughly constant regardless of how deep into the dataset the user navigates.

---

# Why Cursor Pagination Is Stable

Cursor pagination is anchored to an actual row rather than a row position.

Suppose the first page ends at

```
id = 100
```

Now another row is inserted with

```
id = 50
```

The next query still executes

```sql
WHERE id > 100
```

The newly inserted row has no impact on the next page because the cursor always represents a fixed point in the ordered dataset.

This avoids duplicate and missing rows caused by concurrent inserts or deletes.

---

# Composite Cursor

Sometimes the sorting column is not unique.

For example,

```sql
ORDER BY created_at DESC
```

Multiple rows may share the same timestamp.

Using only

```sql
WHERE created_at < ?
```

can produce duplicate or skipped records.

Instead, use a unique tiebreaker.

```sql
ORDER BY created_at DESC, id DESC
```

```sql
WHERE
(created_at, id) < (:last_created_at, :last_id)
```

This guarantees a deterministic ordering across pages.

---

# Token Pagination

Token pagination is built on top of cursor pagination.

Instead of exposing the cursor directly,

```
cursor = 120
```

the server encodes the cursor into an opaque token.

```
cursor = eyJpZCI6MTIwfQ==
```

The client never interprets or modifies this value.

It simply sends it back.

```http
GET /orders?cursor=eyJpZCI6MTIwfQ==
```

The server decodes the token and continues fetching the next page.

This approach allows the server to change the cursor format without affecting clients.

---

# Offset vs Cursor

| Feature | Offset | Cursor |
|----------|---------|---------|
| Implementation | Simple | Moderate |
| Performance on deep pages | Degrades with offset | Consistent |
| Stable under inserts/deletes | No | Yes |
| Supports arbitrary page numbers | Yes | No |
| Suitable for infinite scrolling | No | Yes |
| Typical use case | Admin dashboards | Public APIs |

---

# Which Pagination Strategy Should You Choose?

### Offset Pagination

Use when:

- The dataset is relatively small.
- Users need page numbers.
- Jumping to arbitrary pages is required.
- Data changes infrequently.
- Internal dashboards and reporting tools.

---

### Cursor Pagination

Use when:

- Tables contain millions of rows.
- APIs receive high traffic.
- Data changes frequently.
- Infinite scrolling is used.
- Consistent performance is required.

---

### Token Pagination

Use when:

- Building public APIs.
- Cursor implementation details should remain hidden.
- The server needs flexibility to evolve the cursor format.

---

# Common Mistakes

### Returning Unlimited Data

Never allow

```http
GET /orders?limit=1000000
```

Always enforce a maximum page size on the server.

---

### Sorting by Non-Unique Columns

Always include a unique tiebreaker such as the primary key.

```sql
ORDER BY created_at DESC, id DESC
```

---

### Exposing Cursor Internals

Treat cursors as opaque values.

Clients should never construct or modify them.

---

### Using Offset Pagination for Large Public APIs

Offset pagination is easy to implement but does not scale well for deep pages or frequently changing datasets.

---

# Key Takeaways

- Pagination limits the amount of data returned by an API regardless of dataset size.
- Offset pagination is simple but becomes slower as the offset increases.
- Offset pagination may produce duplicate or missing rows when data changes between requests.
- Cursor pagination anchors results to the last row returned, providing stable and scalable pagination.
- Token pagination is a cursor-based approach that hides pagination details from clients.
- Choose the pagination strategy based on the size of the dataset, traffic patterns, and user experience requirements rather than using a single approach everywhere.