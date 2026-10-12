# Access Tokens & Refresh Tokens

## Prerequisites

Before reading this chapter, you should understand:

- Identity & Authentication
- Sessions
- Cookies
- JWT

---

# Why Do We Need Two Tokens?

Imagine a user logs into your application.

```
Username

+

Password

↓

Authenticated
```

The Authentication Service verifies the credentials and issues a JWT.

```
Login

↓

Generate JWT

↓

Return Token
```

At first glance,

this seems sufficient.

The client now includes the JWT with every request.

```
GET /profile

Authorization: Bearer <JWT>
```

Simple.

Fast.

Stateless.

So why do modern authentication systems introduce another token called a **Refresh Token**?

The answer lies in balancing two competing goals.

```
Security

vs

User Experience
```

---

# The Engineering Problem

Suppose we generate a JWT that never expires.

```
Access Token

↓

Valid Forever
```

Now imagine an attacker steals that token.

```
Attacker

↓

Stolen Token

↓

Unlimited Access
```

Because JWTs are self-contained,

the server cannot distinguish between the legitimate user and the attacker.

The attacker now has permanent access until the signing key changes or the account is disabled.

Clearly,

this isn't acceptable.

---

# The Obvious Solution

A natural solution is

```
Make JWTs Expire
```

For example,

```
Access Token

↓

15 Minutes
```

Now,

even if an attacker steals the token,

its lifetime is limited.

```
Token Stolen

↓

15 Minutes Later

↓

Expired
```

Security improves dramatically.

But another problem appears.

---

# The User Experience Problem

Imagine you're editing a document.

After fifteen minutes,

your Access Token expires.

Should the application interrupt you and display

```
Please log in again.
```

every fifteen minutes?

Obviously not.

That would make the application frustrating to use.

Now we have two conflicting requirements.

```
Short-lived Tokens

↓

Good Security
```

```
Long-lived Sessions

↓

Good User Experience
```

Can we have both?

Yes.

That's exactly why modern authentication systems use two different tokens.

---

# Core Idea

Instead of giving one token multiple responsibilities,

we split those responsibilities.

```
Access Token

↓

Authenticate Requests

↓

Short-lived
```

```
Refresh Token

↓

Obtain New Access Tokens

↓

Long-lived
```

Each token now has a single responsibility.

This follows the same engineering principle we've seen throughout the handbook:

> **A component should have one clear responsibility.**

---

# Why Two Tokens Work

Think of an Access Token as a temporary access badge.

```
Office Building

↓

Temporary Visitor Badge

↓

Valid For Today
```

It allows you to move around the building,

but eventually expires.

Now imagine the Refresh Token as your permanent employee identity.

```
Employee Identity

↓

Request New Visitor Badge

↓

Continue Working
```

You don't use your employee identity to open every office door.

You use it only when you need a new temporary badge.

Authentication systems follow the same idea.

```
Refresh Token

↓

Generate

↓

Access Token

↓

Authenticate Requests
```

---

# Separation of Responsibilities

Instead of one long-lived credential,

we now have two specialized credentials.

| Token | Responsibility |
|--------|----------------|
| Access Token | Authenticate API requests |
| Refresh Token | Obtain a new Access Token |

This separation provides an excellent balance between

- security
- scalability
- user experience

---

# Authentication Lifecycle

The complete lifecycle now looks like this.

```
User Login

↓

Verify Credentials

↓

Generate Access Token

↓

Generate Refresh Token

↓

Return Tokens

↓

Client Uses Access Token

↓

Access Token Expires

↓

Use Refresh Token

↓

Generate New Access Token

↓

Continue Using Application
```

Notice something important.

The user entered their password only once.

Everything after that is handled using tokens.

---

# Design Philosophy

Modern authentication systems separate responsibilities instead of creating one powerful token.

```
Password

↓

Prove Identity Once

↓

Access Token

↓

Authenticate Requests

↓

Refresh Token

↓

Maintain Session
```

Each component has a clearly defined purpose,

making the system easier to secure, reason about, and evolve.

---

# Key Takeaways

- A single long-lived token creates significant security risks.
- A single short-lived token creates a poor user experience.
- Access Tokens and Refresh Tokens solve different problems.
- Access Tokens authenticate requests.
- Refresh Tokens obtain new Access Tokens without requiring the user to log in again.
- Splitting responsibilities creates a more secure and user-friendly authentication system.

---

# Understanding the Two Tokens

At this point, we understand why a single token isn't sufficient.

Now let's understand what each token is responsible for.

Although they are issued together,

they have completely different responsibilities.

```
                 Login

                   │

                   ▼

          Authentication Service

                   │

          ┌────────┴────────┐

          ▼                 ▼

   Access Token      Refresh Token
```

A common interview mistake is thinking that one token is simply a longer-lived version of the other.

That's not true.

They solve different problems.

---

# Access Token

An Access Token is a short-lived credential that proves the user's identity.

Think of it as a temporary identity card.

```
Authenticate User

↓

Generate Access Token

↓

Authenticate API Requests
```

Every authenticated API request carries the Access Token.

```http
GET /profile

Authorization: Bearer <Access Token>
```

The server verifies the token.

If it's valid,

the request is authenticated.

Notice something important.

The Access Token doesn't prove that the user just entered their password.

It proves that

> **The Authentication Service has already verified this user's identity.**

That's a very important distinction.

---

# What Does an Access Token Contain?

In JWT-based systems,

an Access Token typically contains authentication claims.

For example,

```json
{
    "sub": "42",
    "email": "alice@example.com",
    "role": "ADMIN",
    "iat": 1710000000,
    "exp": 1710000900
}
```

Notice what's missing.

```
Password

×

Not Stored
```

```
Password Hash

×

Not Stored
```

```
Sensitive Business Data

×

Not Stored
```

An Access Token should contain only the information required to identify the user and authorize requests.

---

# Why Is the Access Token Short-Lived?

Suppose an attacker steals an Access Token.

```
Attacker

↓

Valid Access Token

↓

Authenticated Requests
```

This is called **token theft**.

If the token never expired,

the attacker could continue using it indefinitely.

Instead,

we intentionally keep Access Tokens short-lived.

Typical expiration times are

```
10 Minutes

15 Minutes

30 Minutes
```

Even if an attacker steals one,

the window of opportunity is limited.

---

# Refresh Token

Now another question appears.

If the Access Token expires every 15 minutes,

how does the user continue using the application?

Should they log in again?

No.

Instead,

the Authentication Service issues a second credential.

```
Refresh Token
```

Unlike the Access Token,

the Refresh Token is **never used to access APIs directly**.

Its only responsibility is

```
Generate New Access Tokens
```

That's it.

Nothing more.

---

# Why Doesn't the Refresh Token Access APIs?

Imagine if every API accepted Refresh Tokens.

```
Refresh Token

↓

GET /orders

↓

Authenticated
```

Now a long-lived credential is travelling with every request.

That significantly increases the attack surface.

Instead,

Refresh Tokens are used only with a dedicated endpoint.

```http
POST /refresh
```

The client exchanges the Refresh Token for a new Access Token.

```
Refresh Token

↓

Authentication Service

↓

New Access Token
```

The Refresh Token never reaches your Orders Service,

Payments Service,

or Inventory Service.

---

# Complete Login Flow

Let's put everything together.

```
                 User

                   │

                   ▼

             POST /login

                   │

                   ▼

         Verify Credentials

                   │

                   ▼

        Generate Access Token

                   │

                   ▼

       Generate Refresh Token

                   │

                   ▼

          Return Both Tokens

                   │

                   ▼

             Client Stores Them
```

At this point,

the client possesses

```
Access Token

↓

Authenticate Requests
```

and

```
Refresh Token

↓

Obtain New Access Tokens
```

Both tokens work together to maintain the user's authenticated session.

---

# Responsibilities

One of the easiest ways to remember the difference is by their responsibilities.

| Access Token | Refresh Token |
|--------------|---------------|
| Authenticates API requests | Generates new Access Tokens |
| Sent with almost every protected request | Sent only to the refresh endpoint |
| Short-lived | Long-lived |
| Optimized for performance | Optimized for session management |
| Usually stateless (JWT) | Usually persisted so it can be revoked |

Notice something.

Neither token replaces the other.

They complement each other.

---

# Why Not Use the Refresh Token Everywhere?

This is a common interview question.

The answer is simple.

A Refresh Token has a much longer lifetime.

If it travelled with every request,

there would be far more opportunities for it to be stolen.

Instead,

the Access Token acts as a disposable credential.

```
Refresh Token

↓

Occasionally Used

↓

Generate

↓

Access Token

↓

Everyday Authentication
```

This design minimizes the exposure of the most valuable credential.

---

# Real-World Analogy

Imagine working in a secure office building.

```
Employee ID

↓

Request Daily Access Badge
```

Your Employee ID is valuable.

You don't swipe it at every office door.

Instead,

you use it to obtain a temporary badge.

```
Temporary Badge

↓

Open Doors

↓

Expires At End Of Day
```

Authentication systems work in a very similar way.

```
Refresh Token

↓

Generate

↓

Access Token

↓

Authenticate Requests
```

The Refresh Token is protected.

The Access Token is disposable.

---

# Key Takeaways

- An Access Token proves that the Authentication Service has already verified the user's identity.
- Access Tokens authenticate protected API requests.
- Access Tokens should contain only the minimum information required for authentication.
- Refresh Tokens never authenticate API requests directly.
- Refresh Tokens exist solely to obtain new Access Tokens.
- Separating these responsibilities improves both security and user experience.

---

# Token Refresh Flow

Eventually,

every Access Token expires.

Suppose the user is actively using your application.

```
Access Token

↓

15 Minutes

↓

Expired
```

The user clicks

```
GET /orders
```

The request reaches the server.

```
Authorization: Bearer <Access Token>
```

The Authentication Middleware verifies the token.

```
Verify Signature

↓

Check exp Claim

↓

Expired
```

The request is rejected.

```http
401 Unauthorized
```

At this point,

the application has two choices.

```
Ask User To Login Again

or

Use Refresh Token
```

Modern applications choose the second option.

---

# Complete Refresh Flow

Instead of asking for the user's password again,

the client sends the Refresh Token.

```http
POST /refresh
```

```json
{
    "refresh_token": "<refresh-token>"
}
```

The Authentication Service performs several checks.

```
Receive Refresh Token

↓

Exists?

↓

Expired?

↓

Revoked?

↓

Belongs To User?

↓

Generate New Access Token
```

If everything succeeds,

a new Access Token is returned.

```
Old Access Token

↓

Expired

↓

Refresh Token

↓

New Access Token

↓

Continue Requests
```

Notice something.

The user's password was never involved.

The Refresh Token acts as proof that the user already authenticated successfully in the past.

---

# Why Doesn't The User Notice?

Most modern applications refresh Access Tokens silently.

The user is editing a document.

```
Access Token

↓

Expires
```

The frontend automatically calls

```
POST /refresh
```

A new Access Token is received.

```
Continue Editing
```

The user never notices that authentication happened behind the scenes.

This creates a smooth user experience while maintaining short-lived Access Tokens.

---

# Refresh Token Rotation

Now imagine Refresh Tokens never changed.

```
Refresh Token

↓

Valid For 30 Days
```

Suppose an attacker steals it.

```
Attacker

↓

Refresh Token

↓

Generate Unlimited Access Tokens

↓

30 Days
```

This is a serious security problem.

Instead,

many production systems rotate Refresh Tokens.

---

# What Is Rotation?

Every successful refresh produces

two new tokens.

```
Old Refresh Token

↓

POST /refresh

↓

New Access Token

+

New Refresh Token
```

Immediately afterwards,

the old Refresh Token becomes invalid.

```
Refresh Token A

↓

Used

↓

Invalid

↓

Refresh Token B

↓

Active
```

Only one Refresh Token remains valid at any point in time.

---

# Why Rotate?

Rotation significantly reduces the usefulness of stolen tokens.

Imagine this timeline.

```
Monday

↓

Refresh Token A

↓

Attacker Steals It
```

Tuesday,

the legitimate user refreshes their session.

```
Refresh Token A

↓

Generate

↓

Refresh Token B
```

Now,

if the attacker later attempts to use

```
Refresh Token A
```

the Authentication Service rejects it.

The stolen token has already become useless.

---

# Refresh Token Reuse Detection

This is one of the most interesting production security features.

Suppose the Authentication Service receives

```
Refresh Token A
```

that was already rotated.

That should never happen.

```
Refresh Token A

↓

Already Used

↓

Why Is It Being Used Again?
```

There are only two possibilities.

1.

A software bug.

2.

Someone else possesses the token.

The second possibility is far more dangerous.

---

# Handling Reuse

When Refresh Token reuse is detected,

many identity providers assume compromise.

```
Refresh Token Reused

↓

Possible Theft

↓

Invalidate All User Refresh Tokens

↓

Force Login

↓

Log Security Event
```

The inconvenience of asking the user to log in again is much smaller than allowing an attacker to keep refreshing sessions.

---

# Sliding Sessions

Another common interview topic.

Suppose Refresh Tokens expire after

```
30 Days
```

Should the user be forced to log in every month,

even if they use the application daily?

Many systems choose a different approach.

```
User Active

↓

Refresh Session

↓

Extend Expiration

↓

Continue
```

Every successful refresh extends the Refresh Token's expiration.

This is known as a **Sliding Session**.

The session continues sliding forward as long as the user remains active.

---

# Absolute Expiration

Sliding forever isn't always desirable.

Imagine an employee remains logged in for five years.

Many organizations enforce an absolute expiration.

Example

```
Sliding Window

↓

30 Days
```

```
Absolute Maximum

↓

180 Days
```

Even if the user remains active,

they must authenticate again after the absolute limit.

This limits long-term risk.

---

# Multi-Device Sessions

Users rarely use only one device.

A user might have

```
Laptop

Phone

Tablet
```

Each device should receive its own Refresh Token.

```
User

↓

Laptop

↓

Refresh Token A
```

```
User

↓

Phone

↓

Refresh Token B
```

```
User

↓

Tablet

↓

Refresh Token C
```

Now,

logging out of the laptop affects only

```
Refresh Token A
```

The phone and tablet remain logged in.

---

# Why This Design Works

Separating Refresh Tokens per device provides several benefits.

- Independent logout
- Device management
- Better security
- Easier compromise detection

Many applications expose a page showing

```
Logged In Devices

MacBook

iPhone

Windows PC
```

Each entry corresponds to a different Refresh Token stored by the Authentication Service.

---

# Common Design Decisions

A production authentication system should:

- Keep Access Tokens short-lived.
- Rotate Refresh Tokens after every successful refresh.
- Detect Refresh Token reuse.
- Support one Refresh Token per device.
- Allow users to revoke sessions individually.
- Support absolute session expiration.

These practices significantly reduce the impact of credential theft while maintaining a seamless user experience.

---

# Key Takeaways

- Access Tokens expire frequently and should be replaced using Refresh Tokens.
- Refresh operations are usually invisible to users.
- Refresh Token rotation ensures that old Refresh Tokens become invalid after use.
- Reuse detection helps identify stolen Refresh Tokens.
- Sliding sessions improve user experience without sacrificing short-lived Access Tokens.
- Issuing one Refresh Token per device enables independent session management and stronger security.

---

# Token Storage Strategies

At this point,

our Authentication Service generates two tokens.

```
Access Token

+

Refresh Token
```

Now another important question appears.

> **Where should these tokens be stored?**

The answer depends entirely on the client application.

For example,

```
Web Browser

↓

Different Strategy
```

```
Mobile Application

↓

Different Strategy
```

```
Desktop Application

↓

Different Strategy
```

There is no universal solution.

Instead,

we choose a storage strategy based on the application's security requirements and threat model.

---

# The Engineering Trade-off

Every storage mechanism tries to balance three competing goals.

```
Security

↓

User Experience

↓

Developer Simplicity
```

Improving one often comes at the cost of another.

For example,

```
Maximum Security

↓

More Complexity
```

or

```
Very Simple Implementation

↓

Higher Risk
```

Engineering is about choosing the right trade-off.

---

# Option 1 - Local Storage

Many Single Page Applications store the Access Token in

```
localStorage
```

```
Browser

↓

localStorage

↓

Access Token
```

Every request manually attaches the token.

```javascript
Authorization: Bearer <Access Token>
```

Advantages

- Very easy to implement.
- Persists across browser refreshes.
- Simple integration with frontend frameworks.

However,

there is an important security concern.

---

# XSS Risk

Suppose an attacker successfully injects JavaScript into your application.

The malicious script can execute

```javascript
localStorage.getItem("access_token")
```

Now the attacker possesses the Access Token.

```
XSS

↓

Read Local Storage

↓

Steal Token

↓

Authenticated Requests
```

This is why many security engineers discourage storing long-lived credentials in Local Storage.

Notice something.

The problem isn't Local Storage itself.

The real problem is

```
XSS

↓

Token Theft
```

---

# Option 2 - HttpOnly Cookies

Another popular strategy is

```
HttpOnly Cookie
```

Instead of returning

```json
{
    "access_token": "..."
}
```

the Authentication Service responds with

```http
Set-Cookie

HttpOnly

Secure
```

The browser stores the cookie automatically.

```
Browser

↓

Cookie Storage

↓

HttpOnly
```

JavaScript cannot read

```
document.cookie
```

This significantly reduces the impact of XSS.

---

# Does HttpOnly Solve Everything?

No.

It protects against one category of attack.

```
XSS

↓

Cannot Read Cookie

✓
```

But another concern appears.

```
Browser

↓

Automatically Sends Cookie
```

If an attacker tricks the browser into sending requests to your application,

the cookie may still be included.

This introduces the possibility of

```
CSRF
```

Fortunately,

modern applications mitigate this using

- SameSite Cookies
- CSRF Tokens
- Double Submit Cookies

We'll study these techniques in the Backend Security section.

---

# Option 3 - Browser Memory

Some applications store the Access Token only in memory.

```
JavaScript Memory

↓

Access Token
```

Advantages

```
Page Refresh

↓

Token Removed
```

An attacker cannot recover it after the page closes.

Disadvantages

Refreshing the page removes the token.

The client must obtain another Access Token using the Refresh Token.

This approach is common in highly security-sensitive applications.

---

# Mobile Applications

Mobile applications are different.

There is no Local Storage.

Instead,

mobile platforms provide secure storage.

Examples

```
iOS

↓

Keychain
```

```
Android

↓

Keystore
```

These systems encrypt credentials using operating system security features.

Applications should avoid storing authentication tokens in plain files or databases.

---

# Where Should the Refresh Token Live?

The Refresh Token is far more valuable than the Access Token.

Remember,

it can generate new Access Tokens.

```
Refresh Token

↓

New Access Token
```

Because of this,

the Refresh Token should receive stronger protection.

Common strategies include

```
Web

↓

HttpOnly Secure Cookie
```

```
Mobile

↓

Keychain / Keystore
```

The Refresh Token should rarely be accessible to JavaScript.

---

# Recommended Storage Strategy

For modern web applications,

a common production approach is

```
Access Token

↓

Memory
```

```
Refresh Token

↓

HttpOnly Cookie
```

The workflow becomes

```
Login

↓

Access Token

↓

JavaScript Memory
```

```
Refresh Token

↓

HttpOnly Cookie
```

When the Access Token expires,

the browser automatically includes the Refresh Token.

```
POST /refresh

↓

New Access Token

↓

Continue Requests
```

The frontend never directly accesses the Refresh Token.

---

# Backend-for-Frontend (BFF)

Some organizations go even further.

Instead of giving the browser JWTs,

they introduce another service.

```
Browser

↓

Backend For Frontend

↓

Authentication Service
```

The browser communicates only with the BFF.

The BFF manages all tokens.

Advantages

- Tokens never reach browser JavaScript.
- Simpler frontend.
- Reduced attack surface.
- Better centralized security.

This pattern is increasingly common in large enterprise applications.

---

# Which Strategy Is Best?

There isn't one correct answer.

The appropriate strategy depends on

- application architecture
- client platform
- threat model
- regulatory requirements
- user experience goals

An experienced engineer should understand the trade-offs rather than memorizing a single recommendation.

---

# Common Interview Questions

### Should Access Tokens be stored in Local Storage?

They can be,

but Local Storage is vulnerable to XSS.

The decision depends on the application's threat model.

---

### Why are Refresh Tokens commonly stored in HttpOnly Cookies?

Because Refresh Tokens are long-lived credentials and should not be directly accessible to JavaScript.

---

### Why not store everything in cookies?

Cookies are automatically attached to requests,

which introduces CSRF considerations.

Proper cookie configuration is required.

---

### Why do many SPAs store Access Tokens only in memory?

It limits the lifetime of stolen credentials and avoids persisting Access Tokens across browser sessions.

---

# Production Best Practices

- Keep Access Tokens short-lived.
- Protect Refresh Tokens more aggressively than Access Tokens.
- Use HttpOnly and Secure for authentication cookies.
- Rotate Refresh Tokens.
- Protect against XSS and CSRF.
- Use secure platform storage on mobile devices.
- Understand the trade-offs instead of following one universal rule.

---

# Key Takeaways

- Token storage is a security design decision, not a framework feature.
- Access Tokens and Refresh Tokens often require different storage strategies.
- Local Storage offers simplicity but increases exposure to XSS.
- HttpOnly Cookies reduce JavaScript access but require CSRF protections.
- Mobile platforms should use secure operating system storage.
- The best solution depends on the application's architecture and threat model.

---

# Common Interview Questions

---

## Why can't we use a single long-lived JWT?

A long-lived JWT becomes a high-value credential.

If an attacker steals it, they can continue making authenticated requests until it expires.

Since JWTs are stateless, the server usually cannot revoke them immediately without introducing additional infrastructure.

Using a short-lived Access Token limits the impact of token theft while the Refresh Token maintains the user's session.

---

## Why not simply increase the Access Token expiration?

Suppose we make Access Tokens valid for

```
365 Days
```

Now the Access Token effectively becomes a permanent password.

If compromised,

the attacker has access for an entire year.

Instead,

modern authentication systems intentionally keep Access Tokens short-lived and issue new ones using Refresh Tokens.

---

## Why are Refresh Tokens stateful?

One of the biggest advantages of JWT Access Tokens is that they are stateless.

```
Receive JWT

↓

Verify Signature

↓

Authenticated
```

No database lookup is required.

Refresh Tokens solve a different problem.

They need to support

- Logout
- Revocation
- Rotation
- Device Management
- Reuse Detection

All of these operations require server-side state.

That's why Refresh Tokens are usually persisted.

---

## Why not verify Refresh Tokens on every request?

Because that's not their responsibility.

Access Tokens authenticate requests.

Refresh Tokens maintain sessions.

If Refresh Tokens were sent with every request,

we would be exposing our most valuable credential far more frequently than necessary.

Instead,

Refresh Tokens are used only with

```
POST /refresh
```

---

## Why is the Access Token usually a JWT?

JWTs are self-contained.

```
Request

↓

JWT

↓

Verify Signature

↓

Authenticated
```

No session lookup is required.

This makes them ideal for high-throughput APIs and distributed systems.

---

## What happens when an Access Token expires?

The API returns

```
401 Unauthorized
```

The client then calls

```
POST /refresh
```

using the Refresh Token.

If the Refresh Token is valid,

the Authentication Service issues a new Access Token.

The user usually doesn't notice this process.

---

## What happens if the Refresh Token expires?

The Authentication Service can no longer issue new Access Tokens.

The user must authenticate again.

This is why users occasionally need to log in again after weeks or months of inactivity.

---

## Can an application revoke an Access Token immediately?

Not usually.

Since Access Tokens are typically stateless,

the server doesn't keep track of every issued token.

Immediate revocation requires additional infrastructure,

such as

- Token blacklists
- Redis
- Token introspection

Many applications instead rely on

- short Access Token lifetimes
- Refresh Token revocation

---

## Why rotate Refresh Tokens?

Suppose

```
Refresh Token A
```

is stolen.

If Refresh Tokens never changed,

the attacker could continue generating new Access Tokens until the Refresh Token expired.

With rotation,

```
Refresh Token A

↓

Used

↓

Refresh Token B

↓

Refresh Token A Invalid
```

The stolen token quickly becomes useless.

---

## What's more valuable?

Access Token

or

Refresh Token?

The Refresh Token.

An Access Token has a short lifetime.

A Refresh Token can generate many future Access Tokens.

That's why Refresh Tokens receive stronger protection.

---

## Should JWT contain permissions?

Stable information is generally acceptable.

Examples

- User ID
- Issuer
- Expiration
- Tenant ID

Frequently changing information,

such as dynamic permissions,

should usually not be embedded in long-lived JWTs because changes won't take effect until the token expires.

Instead,

retrieve permissions from your authorization layer when appropriate.

---

# Common Interview Mistakes

---

### ❌ "Refresh Tokens authenticate requests."

Incorrect.

Refresh Tokens never access business APIs directly.

They exist solely to obtain new Access Tokens.

---

### ❌ "Access Tokens should live for months."

Incorrect.

Long-lived Access Tokens significantly increase the impact of token theft.

---

### ❌ "Refresh Tokens are just long-lived JWTs."

Not necessarily.

Many systems use opaque random strings for Refresh Tokens.

Their implementation is independent of Access Tokens.

---

### ❌ "JWT solves logout."

JWT itself doesn't solve logout.

Logout is typically implemented by invalidating the Refresh Token while allowing existing Access Tokens to expire naturally.

---

### ❌ "Local Storage is always wrong."

Incorrect.

Local Storage has trade-offs.

The appropriate storage mechanism depends on

- client type
- threat model
- application architecture
- security requirements

Good engineers understand trade-offs instead of following absolute rules.

---

### ❌ "HttpOnly cookies eliminate all attacks."

Incorrect.

They mitigate JavaScript access to cookies,

but applications must still defend against attacks such as CSRF.

---

# Production Best Practices

A production authentication system should generally follow these principles.

### Authentication

- Keep Access Tokens short-lived.
- Protect Refresh Tokens aggressively.
- Rotate Refresh Tokens after use.
- Detect Refresh Token reuse.
- Issue one Refresh Token per device.

---

### Token Design

Access Tokens should contain only stable authentication claims.

Avoid embedding

- passwords
- sensitive business information
- frequently changing permissions

---

### Storage

Web Applications

```
Access Token

↓

Memory
```

```
Refresh Token

↓

HttpOnly Secure Cookie
```

Mobile Applications

```
Access Token

↓

Secure Storage
```

```
Refresh Token

↓

Keychain / Keystore
```

---

### Security

- Always use HTTPS.
- Use Secure cookies in production.
- Protect against XSS.
- Protect against CSRF.
- Log authentication events.
- Monitor unusual login activity.

---

# Choosing Between Sessions and JWT

A common misconception is that JWT is always better.

It isn't.

Choose based on your requirements.

| Requirement | Sessions | JWT |
|------------|----------|-----|
| Simple monolithic application | ✅ Excellent | ✅ Good |
| Immediate logout | ✅ Easy | ⚠ Requires additional strategy |
| Horizontal scaling | ⚠ Shared session store | ✅ Excellent |
| Mobile APIs | ⚠ Less common | ✅ Excellent |
| Microservices | ⚠ Additional coordination | ✅ Excellent |
| Stateless architecture | ❌ No | ✅ Yes |

The best solution depends on the architecture,

not on popularity.

---

# Key Takeaways

- Access Tokens and Refresh Tokens solve different problems.
- Access Tokens authenticate requests and should be short-lived.
- Refresh Tokens maintain long-lived user sessions.
- Refresh Tokens should be rotated and protected more aggressively.
- Token storage is an architectural decision based on the application's threat model.
- Modern authentication systems prioritize both security and user experience by separating short-lived authentication from long-lived session management.

---

# Summary

The evolution of modern authentication can be understood as a progression of engineering decisions.

```
Password

↓

Verify Identity

↓

Generate Access Token

↓

Authenticate Requests

↓

Access Token Expires

↓

Use Refresh Token

↓

Generate New Access Token

↓

Continue Session

↓

User Logs Out

↓

Invalidate Refresh Token

↓

Session Ends
```

Each component has exactly one responsibility.

This separation makes authentication systems

- scalable
- secure
- maintainable
- easy to reason about

Understanding **why** these components exist is far more valuable than simply memorizing how they work.