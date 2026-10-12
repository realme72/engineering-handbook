# Identity & Authentication

## Why Do We Even Need Authentication?

Say you're building a banking application. A request hits your API:

```http
POST /transfer-money
```

Before running this, the server has a few obvious questions to answer: who sent it, can I trust them, are they really the account owner, and should they be allowed to move money at all? If it can't answer those, it has no business executing the logic underneath.

Almost every backend request follows the same shape:

```
                Incoming Request

                       │

                       ▼

              Identity Verification

                       │

                       ▼

              Permission Check

                       │

                       ▼

              Execute Business Logic
```

Everything in this section exists to solve one piece of that flow.

---

## Authentication vs Authorization

People mix these two up constantly. The easiest fix is to remember the question each one answers.

Authentication asks

> **Who are you?**

Authorization asks

> **What are you allowed to do?**

Say Alice logs into GitHub. Authentication proves she really is Alice. Later, she tries to delete a private repo — now GitHub asks a different question: does Alice actually have permission to delete this one? That's authorization.

Authentication always comes first, because authorization only makes sense once you know who you're even talking about.

```
Incoming Request

↓

Authentication

↓

Identity Established

↓

Authorization

↓

Business Logic
```

---

## What is Identity?

When a system says "this request belongs to Alice," what does that actually mean under the hood? Alice isn't just a username — she's a bundle of attributes the system tracks:

- User ID
- Email
- Roles
- Permissions
- Organization
- Account Status

Different systems track different fields, but the idea is the same: identity is everything the system knows about whoever's calling it.

---

## Principal

Backend frameworks often call this a **Principal** — the identity attached to the current request. Depending on the system, a principal might be a user, another service, a scheduled job, an administrator, or a machine.

Once authentication succeeds, the framework builds a principal that the rest of the request uses from there on out:

```
Incoming Request

↓

Authenticate

↓

Principal Created

↓

Business Logic
```

You'll run into this exact concept in Spring Security, ASP.NET, Django, FastAPI middleware, and most other serious frameworks.

---

## Credentials

How does the server actually know you're Alice? You present proof — a credential. Depending on the system, that might be a password, a session ID, a JWT, an API key, an OAuth access token, or a client certificate. Authentication is simply the act of verifying that proof. Once it checks out, the server trusts the identity attached to the request.

---

## Stateful vs Stateless Authentication

Here's the real design decision. Alice logs in successfully, and the next request comes in:

```http
GET /profile
```

How does the server remember who she is? Two ways.

### Option 1: The Server Remembers

```
Client

↓

Server

↓

Session Stored
```

This is **stateful authentication**. Sessions live here.

### Option 2: The Client Remembers

```
Client

↓

JWT

↓

Server Verifies

↓

Request Accepted
```

The server keeps no login state at all — the client carries its own identity on every request. This is **stateless authentication**, and it's where JWT lives. We'll dig into both approaches in the chapters ahead.

---

## Authentication Architecture

Every authentication mechanism, no matter how it's implemented, boils down to the same flow:

```
                    Client

                      │

                      ▼

              Send Credentials

                      │

                      ▼

             Authentication Layer

                      │

          Credentials Valid?

             │             │

            No            Yes

             │             │

      Reject Request       ▼

                     Identity Established

                              │

                              ▼

                     Authorization Layer

                              │

                  Permission Granted?

                     │               │

                    No              Yes

                     │               │

              Reject Request         ▼

                           Execute Business Logic
```

Sessions, JWT, OAuth, LDAP, API keys — whatever you're using, this shape barely changes. Only *how* identity gets established changes.

---

## Real-World Example

Say you're building an e-commerce platform. A request comes in:

```http
POST /orders
```

The backend doesn't create the order immediately — it asks who's making this request first. Authentication answers: `User 1024`. Then it asks whether User 1024 is allowed to place orders. Authorization answers: yes. Only then does the order actually get created. Business logic is always the last step, never the first.

---

## What's Next?

With the overall flow in place, we can go mechanism by mechanism:

```
Identity

↓

Authentication

↓

Sessions

↓

Cookies

↓

JWT

↓

Access & Refresh Tokens

↓

OAuth 2.0

↓

OpenID Connect

↓

LDAP / Active Directory

↓

SAML & SSO

↓

Authorization
```

Every chapter from here fits somewhere on this map.

---

## Common Interview Questions

### What's the difference between authentication and authorization?

Authentication verifies **who** the caller is. Authorization determines **what** that authenticated caller is allowed to do.

---

### What is identity?

The information that uniquely represents a caller within a system — a user ID, email, roles, and whatever other attributes the system tracks alongside them.

---

### What is a principal?

The authenticated identity attached to the current request. Depending on the system, it can represent a user, a service, or a machine, not just a human.

---

### What are credentials?

The proof a caller presents to establish identity — a password, a JWT, an API key, a client certificate, whatever the system accepts.

---

### What's the difference between stateful and stateless authentication?

In stateful authentication, the server stores login state — typically a session. In stateless authentication, the client carries its own authentication information, usually a JWT, and the server verifies it fresh on every request.

---

### Does authentication happen before authorization?

Yes. You have to know who someone is before you can decide what they're allowed to do.

---

## Common Interview Mistakes

❌ Using authentication and authorization interchangeably.

✔ Authentication answers **who**. Authorization answers **what**.

---

❌ Thinking JWT is authentication.

✔ JWT is one way of carrying authentication information in a stateless system — not authentication itself.

---

❌ Assuming authentication always means users.

✔ Services, machines, and background jobs authenticate too.

---

## Key Takeaways

- Every protected request starts by establishing identity.
- Authentication verifies identity using credentials.
- Authorization checks permissions after authentication succeeds.
- A principal represents the authenticated identity within the application.
- Authentication can be stateful (sessions) or stateless (JWT).
- Every authentication mechanism ultimately follows the same high-level request flow.
