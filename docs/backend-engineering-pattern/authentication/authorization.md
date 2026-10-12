# Authorization

## Prerequisites

Before reading this chapter, you should understand:

- Identity & Authentication
- Sessions
- Cookies
- JWT
- Authentication System Design

---

# What is Authorization?

Authorization is the process of determining **what an authenticated user is allowed to do**.

Authentication answers:

> **Who are you?**

Authorization answers:

> **What are you allowed to do?**

Authentication always happens first — authorization only makes sense once the user's identity has actually been established.

---

# Why Do We Need Authorization?

Say Alice logs into an application:

```
POST /login

↓

Authentication Successful

↓

JWT Issued
```

She's now authenticated, and makes this request:

```http
DELETE /users/42
```

The server already knows `User = Alice`. But another question shows up immediately: should Alice be allowed to delete someone *else's* account? Authentication can't answer that — it only proved who she is. Authorization is what decides whether the request itself should actually go through.

---

# Authentication vs Authorization

These get confused constantly.

| Authentication | Authorization |
|---------------|---------------|
| Verifies identity | Verifies permissions |
| Answers "Who are you?" | Answers "What are you allowed to do?" |
| Happens first | Happens after authentication |
| Creates an authenticated user | Decides whether the request can continue |
| Returns 401 if it fails | Returns 403 if it fails |

Think of it like walking into an office building. A security guard checking your employee ID is authentication. Trying to walk into the server room afterward and having your badge checked against a clearance list — that's authorization. The first step verifies who you are; the second decides what you're allowed to touch.

---

# Where Does Authorization Happen?

Every protected request goes through roughly the same lifecycle:

```
                  Client

                    │

Authorization: Bearer <JWT>

                    │

                    ▼

          Authentication Middleware

                    │

            Verify Access Token

                    │

                    ▼

             request.user Created

                    │

                    ▼

             Authorization Layer

                    │

           Is User Allowed?

              │            │

             Yes          No

              │            │

              ▼            ▼

      Business Logic     403 Forbidden
```

Notice that business logic only ever runs after *both* authentication and authorization succeed — never before.

---

# How Authorization Works

Once authentication succeeds, the application already knows who's making the request:

```python
request.user = {
    "id": 42,
    "role": "ADMIN"
}
```

Authorization evaluates this before letting the requested operation actually run:

```
Authenticated User

↓

Requested Resource

↓

Requested Action

↓

Permission Check

↓

Allow / Deny
```

---

# What Does Authorization Check?

Different applications lean on different rules. A few common ones:

### Role

```
Role = ADMIN → Delete User → Allowed
```

### Resource Ownership

```
Alice → GET /orders/101 → Owner? → Yes → Allow
Bob   → GET /orders/101 → Owner? → No  → Deny
```

### Permissions

```
Permission = READ_PRODUCTS  → Allowed
Permission = DELETE_USERS   → Denied
```

### Business Rules

Authorization isn't limited to roles — it can enforce whatever rule the business actually needs:

```
Bank Account → Transfer Money → Daily Limit Exceeded → Denied

Employee → Approve Leave → Manager? → Allowed
```

---

# Authorization Flow

A typical request runs through:

```
Client

↓

Authenticate User

↓

Create request.user

↓

Determine Requested Resource

↓

Determine Requested Action

↓

Evaluate Authorization Rules

↓

Allowed?

↓

Execute Business Logic

↓

Return Response
```

---

# Common Authorization Models

### RBAC (Role-Based Access Control)

Permissions attach to roles, and users inherit whatever their assigned role allows:

```
Admin → Create User, Delete User, Update User
```

### ABAC (Attribute-Based Access Control)

Instead of checking roles alone, decisions get evaluated against multiple attributes — department, location, time of day, device, resource owner — whatever the policy actually cares about.

### ACL (Access Control List)

Each resource keeps its own list of who can access it:

```
Document → Alice: Read, Write
        → Bob: Read
```

The check becomes: does the current user show up on this specific resource's list?

---

# Common HTTP Status Codes

| Status Code | Meaning |
|-------------|---------|
| 200 OK | Request allowed |
| 401 Unauthorized | User is not authenticated |
| 403 Forbidden | User is authenticated but lacks permission |

### What's the difference between 401 and 403?

```
401 → Authentication Failed → "Who are you?"
403 → Authentication Succeeded → "You don't have permission."
```

---

# Real-World Examples

### Netflix

A customer can watch a movie. They can't delete one. An administrator can.

### GitHub

A repository owner can delete the repo. A contributor can push code, but can't delete the repository.

### Banking Application

A customer can transfer ₹5,000 without a second thought. Transferring ₹5 crore triggers additional approval. Same customer, same authentication — a completely different authorization outcome, driven entirely by business rules rather than role alone.

---

# Common Interview Questions

## Authentication vs Authorization?

Authentication verifies identity. Authorization verifies permissions. Authentication happens first; authorization only runs once identity is already established.

---

## Where should authorization happen?

Always on the backend. The frontend can hide buttons for a better user experience, but it should never be trusted to actually enforce security — every protected API needs to check permissions server-side, full stop.

---

## Can JWT replace authorization?

No. JWT establishes identity. Authorization decides whether that authenticated identity is allowed to do the specific thing it's asking for. JWT feeds authorization useful information; it doesn't replace the decision itself.

---

## Can authorization happen before authentication?

No — you need to know who someone is before you can decide what they're allowed to do.

---

## Can every authenticated user access every protected API?

No. Authentication only proves identity. Whether that identity can reach a specific resource or perform a specific action is exactly what authorization decides.

---

## Should authorization logic exist in the frontend?

No, not as the actual enforcement. Frontend checks are fine for hiding features a user can't use — but they're a UX convenience, not security. That has to live on the backend.

---

# Common Interview Mistakes

❌ Treating authentication and authorization as the same thing.

They solve different problems.

---

❌ Returning 401 for permission failures.

That should be a 403.

---

❌ Trusting frontend authorization.

It improves UX. It doesn't provide security — only backend enforcement does.

---

❌ Checking only user roles.

Plenty of real systems also need to evaluate resource ownership, business rules, time-based restrictions, organization policy, or subscription tier.

---

# Key Takeaways

- Authentication verifies identity. Authorization verifies permissions.
- Authorization always occurs after successful authentication.
- Every protected request typically follows: Authenticate → Authorize → Execute Business Logic.
- Authorization decisions may be based on roles, permissions, ownership, attributes, or business rules.
- Backend services must always enforce authorization.
- RBAC, ABAC, and ACL are common authorization models, each suited to different application requirements.
