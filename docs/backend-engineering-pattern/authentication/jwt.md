# JWT Authentication
> Interview-Oriented Handbook for SDE2 / Senior Backend Engineers

---

# Table of Contents

1. Authentication Fundamentals
2. Session-Based Authentication
3. Why JWT?
4. JWT Architecture
5. JWT Claims

> **Note:** This is **Part 1** of the handbook. The remaining sections (login flow, middleware, refresh tokens, security, production architecture, interview questions, etc.) continue in Part 2 and Part 3.

---

# 1. Authentication Fundamentals

## What is Authentication?

Authentication is the process of verifying **who a user is**.

Whenever a client sends a request to a backend service, the server must determine whether the caller is a legitimate user or an anonymous client.

For example:

```
POST /transfer-money
```

How does the server know whether the request is actually coming from John?

Authentication answers exactly this question.

> "Can I trust the identity of the person making this request?"

---

## Authentication vs Authorization

These two terms are frequently confused during interviews.

### Authentication

Authentication verifies the identity of a user.

Example:

```
Who are you?
```

The server validates the user's credentials and confirms that the user is John.

---

### Authorization

Authorization determines what the authenticated user is allowed to do.

Example:

```
Can John delete another user's account?
```

John may be authenticated successfully but still not have permission.

---

### Example

```
User logs in
        │
        ▼
Authentication
        │
        ▼
Identity Verified
        │
        ▼
Authorization
        │
        ▼
Permission Check
```

Authentication always happens before authorization.

---

## Stateless vs Stateful Authentication

One of the most common interview questions.

### Stateful Authentication

The server stores authentication information.

Example:

```
Client
   │
   ▼
Session ID
   │
   ▼
Server
   │
Looks up session
from database/Redis
```

Every request requires the server to remember the user.

---

### Stateless Authentication

The server does **not** store user sessions.

Instead, every request contains enough information to identify the user.

```
Client
   │
JWT
   │
   ▼
Server

Verifies token

Done
```

No session lookup is required.

This is the fundamental idea behind JWT.

---

# Interviewer's Perspective

You should be able to answer:

- What is authentication?
- What is authorization?
- Difference between stateful and stateless authentication?
- Why is JWT called stateless?

---

# 2. Session-Based Authentication

Before understanding JWT, it's important to understand the traditional session-based approach.

Interviewers often ask:

> Why was JWT introduced?

The answer begins with sessions.

---

## How Session Authentication Works

### Step 1

User enters credentials.

```
Email
Password
```

---

### Step 2

Client sends request.

```
POST /login

{
    "email":"john@gmail.com",
    "password":"password123"
}
```

---

### Step 3

Server validates credentials.

Usually by comparing the password hash stored in the database.

```
Database

↓

Password Hash

↓

Compare

↓

Success
```

---

### Step 4

Server creates a session.

Example:

```
Session ID

abc123xyz
```

This session is stored in a database or Redis.

```
Session Store

abc123xyz

↓

User ID = 123
Expiry = 30 mins
```

---

### Step 5

The server returns only the Session ID.

```
Set-Cookie

session_id=abc123xyz
```

The browser stores this cookie.

---

### Step 6

Every future request automatically includes the cookie.

```
GET /orders

Cookie:

session_id=abc123xyz
```

---

### Step 7

The server looks up the session.

```
Request

↓

Session ID

↓

Redis / Database

↓

Find User

↓

Authenticated
```

---

## Session Authentication Flow

```
          Login

            │

            ▼

Username + Password

            │

            ▼

Server verifies credentials

            │

            ▼

Create Session

            │

            ▼

Store Session

(Database / Redis)

            │

            ▼

Return Session Cookie

            │

            ▼

Every Request

            │

            ▼

Cookie Sent

            │

            ▼

Lookup Session

            │

            ▼

User Authenticated
```

---

## Advantages of Sessions

### Easy Logout

The server simply deletes the session.

```
DELETE SESSION

Done
```

Immediately logged out.

---

### Immediate Revocation

If an administrator disables an account,

simply delete the session.

No future requests succeed.

---

### Simple Implementation

Most web frameworks provide built-in session management.

---

## Problems with Sessions

This is where interviewers usually expect some discussion.

### 1. Server Memory

The server must store every active session.

```
1 Million Users

↓

1 Million Sessions
```

As users grow, storage requirements also grow.

---

### 2. Horizontal Scaling

Imagine two servers.

```
          Load Balancer

          /         \

         /           \

 Server A          Server B
```

User logs into Server A.

The session exists only there.

Next request reaches Server B.

```
Session Not Found
```

User appears logged out.

---

### Solution

Use a centralized session store.

Usually Redis.

```
         Load Balancer

         /          \

        /            \

Server A          Server B

        \            /

         \          /

           Redis
```

Now every request requires Redis.

---

### 3. Additional Network Call

Every authenticated request becomes:

```
Receive Request

↓

Read Cookie

↓

Query Redis

↓

Find Session

↓

Continue
```

Even a lightweight API now performs an extra lookup.

---

### 4. Mobile Applications

Cookies work naturally with browsers.

For mobile applications and APIs, managing session cookies is less convenient than token-based authentication.

---

# Interviewer's Perspective

If asked:

> Why don't modern APIs always use sessions?

A strong answer includes:

- Server-side storage
- Horizontal scaling challenges
- Additional session lookup
- Better suitability of tokens for APIs and mobile clients

---

# 3. Why JWT?

JWT (JSON Web Token) solves many of the problems associated with session-based authentication.

Instead of storing session information on the server,

the server sends a signed token to the client.

Every request contains that token.

The server verifies the signature.

No session lookup is required.

---

## JWT Authentication Flow

```
Login

    │

    ▼

Verify Credentials

    │

    ▼

Generate JWT

    │

    ▼

Return JWT

    │

    ▼

Client Stores JWT

    │

    ▼

Every Request

Authorization:

Bearer <JWT>

    │

    ▼

Verify Signature

    │

    ▼

Authenticated
```

Notice an important difference.

The server never stores the access token.

This is why JWT is considered **stateless**.

---

## Benefits of JWT

### Better Horizontal Scaling

Since authentication information travels with the request,

any server can validate the token.

```
Load Balancer

      │

 ┌────┴────┐

 ▼         ▼

Server A  Server B

Server C  Server D

All can verify JWT
```

No shared session store is required for access token validation.

---

### Better for APIs

REST APIs are naturally stateless.

JWT aligns well with REST principles because every request is self-contained.

---

### Better for Microservices

Every service can verify the token independently.

No centralized session lookup.

---

## Is JWT Always Better?

No.

This is a common misconception.

For many traditional web applications,

sessions remain a perfectly valid choice.

JWT shines when:

- Building REST APIs
- Mobile applications
- Microservices
- Distributed systems

---

# Interviewer's Perspective

If someone asks:

> Why was JWT introduced?

A good answer is **not**:

> "JWT is more secure."

Instead explain:

- Stateless authentication
- Better scalability
- Easier horizontal scaling
- Works well for APIs
- Suitable for distributed architectures

---

# 4. JWT Architecture

A JWT consists of three parts.

```
Header

.

Payload

.

Signature
```

Example:

```
xxxxx.yyyyy.zzzzz
```

Each section is Base64URL encoded and separated by a period (`.`).

---

## Part 1 - Header

The header contains metadata about the token.

Example:

```json
{
    "alg": "HS256",
    "typ": "JWT"
}
```

### alg

Specifies the signing algorithm.

Example:

```
HS256

RS256
```

We'll discuss these algorithms in Part 3.

---

### typ

Usually:

```
JWT
```

This indicates the token type.

---

## Part 2 - Payload

The payload contains **claims**.

Claims are pieces of information about the user.

Example:

```json
{
    "user_id":123,
    "role":"admin"
}
```

The payload is **not encrypted**.

Anyone possessing the token can decode it.

Therefore,

never store:

- Passwords
- Credit card numbers
- OTPs
- API Keys
- Secrets

---

## Part 3 - Signature

The signature proves that the token has not been modified.

Conceptually:

```
Header

+

Payload

+

Secret Key

↓

Signing Algorithm

↓

Signature
```

When a request arrives,

the server performs the same signing operation again.

If the generated signature matches the incoming signature,

the token is valid.

Otherwise,

the request is rejected.

---

## Why Can't Someone Change the Payload?

Suppose the payload is:

```
role=user
```

An attacker changes it to:

```
role=admin
```

The payload has changed.

However,

the signature still corresponds to the old payload.

During verification:

```
Incoming Signature

≠

Generated Signature
```

The server rejects the request.

This is the primary purpose of the signature.

---

## Is JWT Encrypted?

No.

This is one of the most frequently asked interview questions.

JWT is:

```
Base64URL Encoded
```

It is **not encrypted**.

Anyone can decode:

- Header
- Payload

Only the signature prevents tampering.

Think of it this way:

```
Encoding

↓

Readable by anyone

Encryption

↓

Readable only with a decryption key
```

JWT uses encoding for transport and signing for integrity, not encryption for secrecy.

---

# Interviewer's Perspective

Know the difference between:

- Encoding
- Encryption
- Signing

Many candidates incorrectly say JWT is encrypted.

It is not.

---

# 5. JWT Claims

Claims are pieces of information stored inside the payload.

They describe the authenticated user or the token itself.

Example:

```json
{
    "sub":"123",
    "role":"admin",
    "exp":1730000000
}
```

Claims fall into three categories.

- Registered Claims
- Public Claims
- Private Claims

---

## Registered Claims

These are standardized claim names defined by the JWT specification.

They are optional but widely used.

---

### sub (Subject)

Represents the identity of the user.

Example:

```json
{
    "sub":"123"
}
```

Usually this is the user's unique identifier.

---

### iss (Issuer)

Identifies who generated the token.

Example:

```json
{
    "iss":"auth-service"
}
```

Useful when multiple authentication providers exist.

---

### aud (Audience)

Indicates which application or service should accept the token.

Example:

```json
{
    "aud":"payment-service"
}
```

This prevents a token intended for one service from being accepted by another.

---

### exp (Expiration Time)

Defines when the token expires.

Example:

```json
{
    "exp":1730000000
}
```

Once expired,

the server should reject the token.

---

### iat (Issued At)

Stores when the token was created.

Useful for debugging and token age calculations.

---

### nbf (Not Before)

Defines when the token becomes valid.

Before this time,

the token should not be accepted.

---

### jti (JWT ID)

A unique identifier for the token.

Example:

```json
{
    "jti":"8b2fd9a4"
}
```

Often used for:

- Token revocation
- Blacklisting
- Refresh token rotation

---

## Custom Claims

Applications often add their own claims.

Example:

```json
{
    "user_id":123,
    "role":"admin",
    "tenant_id":45
}
```

Keep custom claims minimal.

A larger token increases request size because the JWT is sent with every authenticated request.

---

## What Should Be Stored?

Good examples:

- User ID
- Role
- Permissions (if small)
- Tenant ID
- Organization ID

---

## What Should NOT Be Stored?

Never store:

- Passwords
- Refresh Tokens
- API Keys
- OTPs
- Credit Card Numbers
- Personal secrets

Remember:

Anyone can decode the payload.

---

# Interviewer's Perspective

A very common interview question is:

> What information would you put inside a JWT?

A strong answer is:

> "Only information required by downstream services to identify the user and make authorization decisions. Sensitive or confidential data should never be stored because the payload is only encoded, not encrypted."

---

---

# 6. Complete Login Flow

Now that we understand what JWT is, let's see how authentication is implemented in a real backend application.

This is one of the most common interview discussions because it tests whether you've actually built an authentication system.

---

## High-Level Flow

```
                Login Request
                      │
                      ▼
          Validate Email & Password
                      │
                      ▼
          Generate Access Token
                      │
                      ▼
         Generate Refresh Token
                      │
                      ▼
     Store Refresh Token (Database)
                      │
                      ▼
 Return Access + Refresh Token to Client
```

Let's understand each step.

---

## Step 1: User Sends Credentials

The client sends a login request.

```
POST /login

{
    "email": "john@gmail.com",
    "password": "password123"
}
```

---

## Step 2: Validate User

The server searches for the user.

```
SELECT * FROM users
WHERE email = 'john@gmail.com'
```

If the user doesn't exist:

```
401 Unauthorized
```

---

## Step 3: Verify Password

Passwords should **never** be stored in plain text.

Instead, during registration:

```
password

↓

bcrypt / Argon2

↓

Hashed Password
```

Database stores:

```
$2b$12$...
```

During login:

```
Incoming Password

↓

Hash using same algorithm

↓

Compare with stored hash

↓

Match ?

↓

Authenticated
```

Notice something important.

The server never decrypts passwords.

It only compares hashes.

---

# Interviewer's Perspective

**Question**

> Why don't we encrypt passwords instead of hashing them?

Expected Answer:

Encryption is reversible.

Hashing is one-way.

The server never needs to know the original password.

---

## Step 4: Generate Access Token

After successful authentication:

```
{
    "sub": "123",
    "role": "admin",
    "exp": ...
}
```

The server signs the payload.

Result:

```
eyJhbGciOi...
```

This becomes the Access Token.

---

## Step 5: Generate Refresh Token

A refresh token is also generated.

Unlike access tokens,

refresh tokens are usually long random strings.

Example:

```
adf78sdf98sdf...
```

or another JWT depending on the implementation.

---

## Step 6: Store Refresh Token

Unlike access tokens,

refresh tokens are usually stored.

```
Refresh Token

↓

Database

↓

User ID

↓

Expiry

↓

Device

↓

Revoked?
```

Many production systems store a **hash** of the refresh token instead of the raw token.

This minimizes the impact if the database is compromised.

---

## Step 7: Return Tokens

```
Access Token

15 minutes

+

Refresh Token

30 days
```

These are sent back to the client.

---

# Complete Login Flow

```
Client

    │

POST /login

    │

    ▼

Authentication Service

    │

Find User

    │

Verify Password

    │

Generate Access Token

    │

Generate Refresh Token

    │

Store Refresh Token

    │

Return Tokens

    │

    ▼

Client Stores Tokens
```

---

# 7. Where Should Tokens Be Stored?

This is one of the most frequently asked interview questions.

There is no universal answer.

It depends on the client.

---

## Option 1: Local Storage

```
Browser

↓

localStorage
```

Advantages

- Easy to implement
- Survives page refresh

Disadvantages

- Vulnerable to XSS attacks
- JavaScript can read the token

Generally **not recommended** for sensitive applications.

---

## Option 2: Session Storage

```
sessionStorage
```

Advantages

- Cleared when the browser tab closes

Disadvantages

- Still accessible via JavaScript
- Vulnerable to XSS

---

## Option 3: HttpOnly Cookies (Recommended)

```
Set-Cookie

HttpOnly

Secure

SameSite=Lax
```

Advantages

- JavaScript cannot read the cookie
- Better protection against token theft via XSS

Disadvantages

- Cookies are automatically sent by the browser
- Requires CSRF protection

---

# Local Storage vs HttpOnly Cookies

| Feature | Local Storage | HttpOnly Cookie |
|----------|--------------|----------------|
| Accessible via JavaScript | ✅ Yes | ❌ No |
| Vulnerable to XSS token theft | High | Low |
| Automatically sent by browser | ❌ No | ✅ Yes |
| Needs CSRF protection | ❌ No | ✅ Yes |

---

# Interviewer's Perspective

If asked:

> Where would you store JWT?

A good answer:

> For browser-based applications, I prefer HttpOnly Secure cookies because JavaScript cannot access them. If cookies are used, I also enable SameSite and CSRF protection. For mobile apps, secure platform-specific storage such as the iOS Keychain or Android Keystore is typically used.

---

# 8. Authentication Middleware

Every protected API should pass through authentication middleware.

Instead of checking authentication in every controller,

we centralize it.

---

## Middleware Flow

```
Incoming Request

        │

Authorization Header

        │

Extract Token

        │

Verify Signature

        │

Check Expiry

        │

Extract Claims

        │

Attach User

        │

Next Middleware

        │

Controller
```

---

## Authorization Header

Clients send:

```
Authorization:

Bearer <JWT>
```

Example:

```
Authorization:

Bearer eyJhbGciOi...
```

---

## Token Extraction

Middleware extracts:

```
eyJhbGciOi...
```

If missing:

```
401 Unauthorized
```

---

## Verify Signature

The server recalculates the signature.

```
Incoming JWT

↓

Header

↓

Payload

↓

Secret Key

↓

Generate Signature Again

↓

Compare
```

If the signatures don't match,

reject the request.

---

## Check Expiration

```
Current Time

>

exp ?

```

If yes:

```
401 Unauthorized
```

---

## Extract Claims

After verification:

```
{
    "sub":"123",
    "role":"admin"
}
```

Now the application knows:

- User ID
- Role
- Tenant
- Organization

---

## Attach User to Request

Many frameworks attach the authenticated user.

Example:

```
request.user.id

request.user.role
```

Controllers no longer need to parse JWTs.

---

## Controller

```
GET /orders

↓

request.user.id

↓

Load Orders
```

Simple and clean.

---

# Interviewer's Perspective

Don't say:

> Every controller validates JWT.

Instead explain:

Authentication is handled once in middleware.

Controllers only use the authenticated user.

---

# 9. Access Token vs Refresh Token

One of the most important interview topics.

---

## Why Not Make Access Tokens Valid Forever?

Suppose:

```
Access Token

365 days
```

If stolen,

an attacker has access for an entire year.

That's dangerous.

---

## Short-Lived Access Tokens

Instead:

```
Access Token

15 minutes
```

Even if stolen,

damage is limited.

---

## But Users Shouldn't Login Every 15 Minutes

That's where refresh tokens help.

```
Access Token

15 mins

Refresh Token

30 days
```

---

## Authentication Flow

```
Login

↓

Access Token

+

Refresh Token

↓

API Calls

↓

Access Token Expires

↓

Refresh Endpoint

↓

New Access Token

↓

Continue
```

---

## Refresh Endpoint

Example:

```
POST /refresh
```

Client sends:

```
Refresh Token
```

The server verifies it.

If valid,

a new access token is issued.

---

## Why Store Refresh Tokens?

Access Tokens are stateless.

Refresh Tokens usually are not.

Database:

```
Refresh Token

↓

User ID

↓

Expiry

↓

Revoked

↓

Device
```

Now logout becomes possible.

---

# Interviewer's Perspective

If asked:

> Why don't we use only refresh tokens?

Expected Answer:

Refresh tokens are long-lived and should be used sparingly.

Every API request should use a short-lived access token.

---

# 10. Refresh Token Rotation

Many companies implement refresh token rotation.

Instead of reusing the same refresh token forever,

every refresh generates a new one.

---

## Without Rotation

```
Refresh Token

↓

Used

↓

Still Valid
```

If stolen,

an attacker can continue using it.

---

## With Rotation

```
Refresh Token A

↓

Used

↓

Invalidated

↓

Refresh Token B

↓

Used

↓

Invalidated

↓

Refresh Token C
```

Only the latest token remains valid.

---

## Reuse Detection

Suppose:

An attacker steals Refresh Token A.

```
User

↓

Refresh

↓

Gets Token B
```

Later,

the attacker tries using Token A.

```
Refresh Token A

↓

Already Revoked

↓

Possible Token Theft
```

The server can immediately revoke the entire refresh token family and require the user to log in again.

This is called **refresh token reuse detection**.

---

# Interviewer's Perspective

Senior interviewers love this topic because it shows production experience.

Mentioning refresh token rotation immediately differentiates you from candidates who have only implemented basic JWT authentication.

---

# 11. Logout

A classic interview question.

> JWT is stateless.

> So how does logout work?

---

## Problem

Access Tokens are self-contained.

The server doesn't store them.

Therefore:

```
Logout

↓

How do we invalidate the JWT?
```

---

## Option 1: Wait for Expiry

If access token expires in:

```
15 minutes
```

Logout simply deletes it from the client.

Worst case:

The token remains usable until expiry.

This is the simplest and most common strategy.

---

## Option 2: Blacklisting

Store revoked token IDs.

```
Redis

↓

jti

↓

Revoked
```

Every request:

```
Verify JWT

↓

Check Redis

↓

Blocked?
```

Disadvantage:

JWT is no longer completely stateless because every request now requires a blacklist lookup.

---

## Option 3: Revoke Refresh Token (Most Common)

```
Logout

↓

Delete Refresh Token

↓

Access Token Expires Naturally
```

This is how most production systems implement logout.

---

# Interviewer's Perspective

If asked:

> Can JWT be immediately revoked?

Answer:

Not by itself.

Common approaches include:

- Short-lived access tokens
- Refresh token revocation
- Blacklists for special cases

---

# 12. Common Authentication APIs

Typical backend APIs:

```
POST /register

POST /login

POST /refresh

POST /logout

GET /me
```

---

## /register

Creates a new user.

Stores hashed password.

---

## /login

Verifies credentials.

Returns access token and refresh token.

---

## /refresh

Validates refresh token.

Issues a new access token.

Often rotates the refresh token as well.

---

## /logout

Deletes or revokes refresh token.

---

## /me

Returns authenticated user information.

Authentication middleware has already populated the user context.

---

---

# 13. JWT Security

Authentication is not only about generating tokens.

A secure authentication system should also defend against common attack vectors.

Senior interviewers often ask scenario-based questions instead of asking how JWT works.

---

## Attack 1: Token Tampering

Suppose an attacker has the following payload:

```json
{
    "sub": "123",
    "role": "user"
}
```

The attacker changes it to:

```json
{
    "sub": "123",
    "role": "admin"
}
```

Will it work?

**No.**

Why?

Because changing the payload changes the signature.

The server recalculates the signature during verification.

```
Incoming Signature

≠

Generated Signature

↓

401 Unauthorized
```

The request is rejected.

---

## Attack 2: Reading JWT Contents

Many developers believe JWT is encrypted.

It is not.

Anyone can decode:

- Header
- Payload

For example:

```json
{
    "sub":"123",
    "role":"admin",
    "email":"john@gmail.com"
}
```

This information is visible to anyone possessing the token.

Therefore:

Never store

- Passwords
- API Keys
- OTPs
- Credit Card Numbers
- Secrets

inside a JWT.

JWT guarantees **integrity**, not **confidentiality**.

---

## Attack 3: Token Theft

Suppose an attacker steals a user's access token.

Can they use it?

Yes.

Until it expires.

That's why access tokens should have a short lifetime.

Example:

```
10-15 minutes
```

The shorter the expiry,

the smaller the impact of token theft.

---

## Attack 4: XSS (Cross Site Scripting)

Suppose the application stores JWT in Local Storage.

Malicious JavaScript executes:

```javascript
localStorage.getItem("token")
```

The attacker now owns the JWT.

---

### Protection

Use:

```
HttpOnly Cookies
```

JavaScript cannot read HttpOnly cookies.

Even if XSS exists,

stealing the token becomes significantly harder.

---

## Attack 5: CSRF (Cross Site Request Forgery)

Cookies are automatically sent by browsers.

An attacker tricks the user into visiting:

```
evil.com
```

The browser automatically includes authentication cookies.

The victim unknowingly performs authenticated actions.

---

### Protection

Use:

- SameSite=Lax or Strict
- CSRF Tokens
- Origin validation

Remember:

```
Local Storage

↓

XSS Risk

Cookies

↓

CSRF Risk
```

There is no perfect storage mechanism.

Every option has tradeoffs.

---

## Attack 6: Secret Key Leakage

Suppose your JWT secret leaks.

An attacker can now generate valid JWTs.

This is one of the most severe security incidents.

---

### Protection

- Store secrets in Secret Managers
- Never hardcode secrets
- Rotate secrets regularly
- Use strong random keys

Examples:

- AWS Secrets Manager
- HashiCorp Vault
- Kubernetes Secrets

---

## Attack 7: Replay Attack

Suppose someone captures a valid JWT.

They replay it multiple times.

```
Captured Token

↓

Reuse

↓

Reuse

↓

Reuse
```

The server cannot distinguish the original request from the replay.

---

### Mitigation

Usually handled through:

- Short-lived access tokens
- HTTPS
- Token expiration
- Refresh token rotation

---

# Interviewer's Perspective

A common interview question:

> If I steal your JWT, can I impersonate you?

Answer:

Yes.

JWT is a bearer token.

Whoever possesses it can use it until it expires or is revoked.

---

# 14. HS256 vs RS256

Almost every senior backend interview asks this question.

---

## HS256

HS256 uses a **single shared secret**.

```
Secret Key

↓

Sign JWT

↓

Verify JWT
```

The same secret is used for:

- Signing
- Verification

---

### Advantages

- Simple
- Fast
- Easy to implement

---

### Disadvantages

Every service that verifies JWT must know the secret.

If one service is compromised,

an attacker can generate valid tokens.

---

## RS256

RS256 uses two keys.

```
Private Key

↓

Sign JWT

↓

Public Key

↓

Verify JWT
```

Only the Authentication Service owns the private key.

Every other service has only the public key.

---

### Advantages

Compromising an API service does not expose the signing key.

This makes RS256 a better choice for distributed systems.

---

### Disadvantages

- More complex
- Slightly slower
- Requires key management

---

## Which Should You Use?

### Small Application

```
Single Backend

↓

HS256
```

Perfectly acceptable.

---

### Microservices

```
Authentication Service

↓

Private Key

↓

API Gateway

↓

Order Service

↓

Payment Service

↓

Inventory Service

↓

Public Key
```

RS256 is usually preferred.

---

# Interviewer's Perspective

Don't answer:

> RS256 is more secure.

Instead explain:

RS256 separates signing and verification.

Only one service signs tokens.

Every other service only verifies them.

---

# 15. JWT in Microservices

Suppose your application has:

```
User Service

Order Service

Payment Service

Inventory Service
```

Without JWT,

every service needs to query a centralized session store.

```
Service

↓

Redis

↓

User
```

This creates unnecessary network calls.

---

## With JWT

```
Incoming Request

↓

JWT

↓

Verify Signature

↓

Extract User

↓

Continue
```

Each service can authenticate requests independently.

---

## API Gateway

Many organizations authenticate requests at the API Gateway.

```
Client

↓

API Gateway

↓

Verify JWT

↓

Forward Request

↓

Backend Services
```

Backend services receive already authenticated requests.

Some organizations still verify JWT inside services for defense in depth.

---

# Interviewer's Perspective

If asked:

> Where should JWT validation happen?

A good answer:

Usually at the API Gateway.

Critical internal services may also verify tokens before processing requests.

---

# 16. Production Best Practices

These are the practices commonly followed in production systems.

---

## Keep Access Tokens Short

```
10-15 Minutes
```

---

## Refresh Tokens Longer

```
7-30 Days
```

---

## Rotate Refresh Tokens

Never allow the same refresh token to live forever.

---

## Store Refresh Tokens Securely

Prefer storing:

```
Hash(refresh_token)
```

instead of the raw token.

---

## Always Use HTTPS

JWT should never travel over HTTP.

---

## Validate Everything

Always verify:

- Signature
- Expiration
- Issuer
- Audience

Don't rely only on signature verification.

---

## Never Trust Client Claims Blindly

A valid JWT only proves the token was issued by you.

It doesn't mean the user's permissions haven't changed.

For highly sensitive operations,

many systems reload roles/permissions from the database.

Example:

```
Delete Organization

↓

Database Permission Check
```

instead of trusting:

```
role=admin
```

inside the JWT.

---

## Log Authentication Events

Useful logs include:

- Successful login
- Failed login
- Refresh token reuse
- Logout
- Multiple failed attempts

---

## Rate Limit Authentication APIs

Protect:

```
/login

/register

/refresh
```

against brute-force attacks.

---

# 17. JWT vs Session Authentication

| Feature | Session | JWT |
|----------|---------|-----|
| Server Stores State | ✅ Yes | ❌ No (Access Token) |
| Horizontal Scaling | Harder | Easier |
| Logout | Simple | More Complex |
| Database Lookup Every Request | Usually Yes | Usually No |
| Mobile Friendly | Moderate | Excellent |
| Microservices | Less Suitable | Very Suitable |
| Token Revocation | Easy | Requires Strategy |

---

## Which Should You Choose?

Choose Sessions when:

- Traditional server-rendered applications
- Simpler architecture
- Immediate logout required

Choose JWT when:

- REST APIs
- Mobile applications
- Microservices
- Distributed systems

Neither approach is universally better.

Choose based on your architecture.

---

# 18. How I Would Build JWT Authentication

This is probably the most valuable section for interviews.

If an interviewer asks:

> How would you implement authentication from scratch?

A good answer could be:

---

### Step 1

User submits email and password.

```
POST /login
```

---

### Step 2

Validate credentials.

```
Find User

↓

Verify Password Hash
```

---

### Step 3

Generate:

- Access Token
- Refresh Token

---

### Step 4

Store:

```
Hash(Refresh Token)

↓

Database

↓

User

↓

Expiry

↓

Device

↓

Revoked
```

---

### Step 5

Return:

- Access Token
- Refresh Token

inside secure HttpOnly cookies.

---

### Step 6

Every protected request passes through authentication middleware.

Middleware:

- Extracts token
- Verifies signature
- Checks expiration
- Validates issuer and audience
- Attaches authenticated user

---

### Step 7

Controllers use:

```
request.user
```

instead of parsing JWT again.

---

### Step 8

When access token expires:

```
POST /refresh
```

Generate:

- New Access Token
- New Refresh Token (rotation)

Invalidate the old refresh token.

---

### Step 9

Logout:

Delete or revoke refresh token.

Access token expires naturally after a few minutes.

---

## Complete Production Flow

```
                  Login
                    │
                    ▼
          Authentication Service
                    │
      ┌─────────────┴──────────────┐
      ▼                            ▼
Access Token                 Refresh Token
(15 mins)                    (30 days)
      │                            │
      ▼                            ▼
 HttpOnly Cookie          Database (Hashed)
      │
      ▼
 API Gateway / Middleware
      │
 Verify Signature
 Check Expiry
 Validate Claims
      │
      ▼
 request.user
      │
      ▼
 Business Logic
```

---

# 19. Common Interview Questions

## Why is JWT stateless?

Because the server does not store access token state.

The token itself contains the information required for authentication.

---

## Why not store passwords inside JWT?

JWT payload is only encoded.

Anyone can decode it.

---

## Why use Refresh Tokens?

To keep access tokens short-lived without forcing users to log in frequently.

---

## Why store Refresh Tokens in the database?

To support:

- Logout
- Revocation
- Rotation
- Multi-device management

---

## Can JWT be modified?

Yes.

But modification invalidates the signature,

so verification fails.

---

## Is JWT encrypted?

No.

It is encoded and digitally signed.

---

## Why not use long-lived Access Tokens?

If stolen,

the attacker gains long-term access.

---

## Can JWT be revoked?

Not directly.

Typical approaches:

- Short expiry
- Refresh token revocation
- Blacklisting

---

## Why use HttpOnly Cookies?

To reduce token theft through XSS.

---

## Why use RS256 in Microservices?

Only the Authentication Service owns the private key.

Other services only verify tokens using the public key.

---

# 20. Backend Cheat Sheet

Remember these points before an interview.

✅ Authentication verifies identity.

✅ Authorization verifies permissions.

✅ JWT is stateless because the server doesn't store access token state.

✅ JWT consists of:

- Header
- Payload
- Signature

✅ Payload is encoded, not encrypted.

✅ Signature prevents tampering.

✅ Access Tokens should be short-lived.

✅ Refresh Tokens should be stored securely and rotated.

✅ Store browser tokens in HttpOnly Secure Cookies.

✅ Protect cookies against CSRF.

✅ Protect Local Storage applications against XSS.

✅ Use HTTPS everywhere.

✅ HS256 uses one shared secret.

✅ RS256 uses a public/private key pair.

✅ Authentication belongs in middleware.

✅ Controllers should use `request.user`.

✅ Refresh token revocation enables logout.

✅ JWT is excellent for REST APIs and microservices.

---
