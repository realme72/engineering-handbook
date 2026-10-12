# Authentication System Design

## Prerequisites

Before reading this chapter, you should understand:

- Identity & Authentication
- Sessions
- Cookies
- JWT
- Access Tokens & Refresh Tokens

---

# Why Do We Need an Authentication System?

Most developers think authentication is simply:

```
Username + Password

↓

JWT

↓

Done
```

In reality, that's only a small part of the system.

A production authentication system is responsible for much more than verifying credentials.

It must answer questions like:

- How do we verify a user's identity?
- How do we issue authentication tokens?
- How do we authenticate every future request?
- How do users log out?
- How do we revoke access?
- How do we support multiple devices?
- How do we reset passwords?
- How do we scale to millions of users?

JWT is only one building block.

Authentication is an entire subsystem.

---

# The Engineering Problem

Imagine you're building Netflix.

At first, your application looks simple.

```
           Client

              │

              ▼

        Backend Server

              │

              ▼

          PostgreSQL
```

A user logs in.

The backend verifies the username and password.

Done.

Now your application grows.

```
                  Internet

                     │

                     ▼

              Load Balancer

        ┌────────────┼────────────┐

        ▼            ▼            ▼

    API Server   API Server   API Server

        │            │            │

        └────────────┼────────────┘

                     ▼

              Authentication

                  Database
```

Then your product expands.

You now have

- Mobile Apps
- Web Application
- Smart TVs
- Internal Admin Portal
- Partner APIs
- Microservices

Every incoming request must answer one simple question:

> **Who is making this request?**

That sounds simple.

At scale, it's one of the most important problems in backend engineering.

---

# Responsibilities of an Authentication System

Authentication is much more than login.

A production authentication system is responsible for:

```
Register User

↓

Verify Credentials

↓

Issue Tokens

↓

Authenticate Requests

↓

Authorize Resources

↓

Refresh Tokens

↓

Logout

↓

Revoke Access

↓

Manage Devices

↓

Password Reset
```

Every modern backend application implements some variation of this lifecycle.

---

# High-Level Architecture

A typical authentication system consists of several independent components.

```
                   Client
                      │
                      ▼
               API Gateway
                      │
                      ▼
          Authentication Service
          ┌───────────┼────────────┐
          ▼           ▼            ▼
     User Service  Token Service  Session/Token Store
          │           │            │
          └───────────┼────────────┘
                      ▼
                 PostgreSQL
```

Each component has a single responsibility.

---

# Component Responsibilities

## API Gateway

The API Gateway is the first entry point into the system.

Responsibilities:

- Accept incoming requests
- Forward authentication requests
- Validate JWTs (in some architectures)
- Route requests to downstream services
- Apply rate limiting

---

## Authentication Service

This service owns the authentication logic.

Responsibilities:

- Register users
- Verify passwords
- Generate access tokens
- Generate refresh tokens
- Handle logout
- Rotate refresh tokens

Notice something.

Business services should never contain authentication logic.

Authentication belongs in its own service or module.

---

## User Service

Responsible for user-related operations.

Examples:

- Create users
- Update profile
- Change password
- Lock accounts
- Verify email

It does **not** generate JWTs.

---

## Token Service

Responsible for token lifecycle.

Responsibilities:

- Generate JWTs
- Verify JWTs
- Refresh access tokens
- Rotate refresh tokens
- Revoke tokens (if required)

Separating token logic makes the system easier to maintain and test.

---

## Database

Stores persistent authentication data.

Examples:

- Users
- Password hashes
- Refresh tokens
- Device sessions
- Audit logs

Notice that access tokens (JWTs) are typically **not** stored in the database.

They're self-contained and verified cryptographically.

---

# Request Lifecycle

Every authenticated request follows a predictable lifecycle.

```
Client

↓

Authentication Information

↓

API Gateway

↓

Authentication Middleware

↓

Identity Established

↓

Authorization

↓

Business Logic

↓

Database

↓

Response
```

Authentication always happens before business logic.

If authentication fails,

the request never reaches your application code.

---

# Design Principle

One of the biggest mistakes in backend systems is scattering authentication logic across different services.

For example,

❌

```
Orders Service

↓

Verify JWT
```

```
Payments Service

↓

Verify JWT
```

```
Profile Service

↓

Verify JWT
```

Now every service implements authentication differently.

Instead,

authentication should be centralized.

```
Incoming Request

↓

Authentication Layer

↓

Authenticated User

↓

Business Services
```

Every service receives an already authenticated request and focuses only on business logic.

This separation of concerns keeps the system simpler, more consistent, and easier to evolve.

---

# Key Takeaways

- Authentication is a complete subsystem, not just JWT generation.
- JWT, Sessions, Cookies, and Refresh Tokens are individual building blocks.
- Authentication should be centralized rather than duplicated across services.
- Every authenticated request follows the same high-level lifecycle:
  Authenticate → Authorize → Execute Business Logic.
- Separating responsibilities into dedicated components improves scalability, maintainability, and security.

---

# Token Generation

At this point,

the user's identity has been verified.

The server now knows two things.

1. The credentials are valid.
2. The user is who they claim to be.

The next question is

> **How do we avoid asking the user to enter their password for every request?**

The obvious solution would be

```
Login

↓

Return User ID

↓

Client Sends User ID

↓

Authenticated
```

Obviously this doesn't work.

Anyone could change

```
user_id = 5
```

to

```
user_id = 1
```

and become another user.

The server needs to return something that

- identifies the user
- cannot be forged
- can be verified efficiently

That's exactly why we generate authentication tokens.

---

# Authentication Tokens

After successful login,

the Authentication Service generates two tokens.

```
Access Token

↓

Short-lived

↓

Used on every request
```

```
Refresh Token

↓

Long-lived

↓

Used only to obtain a new Access Token
```

Notice something.

These tokens solve completely different problems.

Access Tokens are optimized for

```
Performance
```

Refresh Tokens are optimized for

```
Security
```

We'll study both in detail later.

For now,

think of them as having different responsibilities.

---

# Login Flow

The complete login flow now becomes

```
                 User

                   │

                   ▼

             POST /login

                   │

                   ▼

         Validate Request

                   │

                   ▼

         Find User By Email

                   │

                   ▼

      Verify Password Hash

                   │

          Valid Credentials?

             │            │

            No           Yes

             │            │

      Return 401          ▼

                 Generate Tokens

                   │

                   ▼

       Store Refresh Token

                   │

                   ▼

          Return Response
```

Notice that

JWT generation is only one small step.

Most of the work happens before that.

---

# Why Two Tokens?

A very common interview question.

Why not simply generate one JWT?

Imagine an Access Token that never expires.

```
Access Token

↓

Valid Forever
```

Now imagine an attacker steals it.

```
Attacker

↓

Valid Token

↓

Unlimited Access
```

The damage is enormous.

Now consider another approach.

```
Access Token

↓

15 Minutes
```

Much safer.

But another problem appears.

Will users have to log in every 15 minutes?

Obviously not.

That's why we introduce a second token.

```
Access Token

↓

Short-lived

↓

Authentication
```

```
Refresh Token

↓

Long-lived

↓

Generate New Access Token
```

Together,

they provide both

- security
- good user experience

---

# Generating the Access Token

After successful authentication,

the Authentication Service builds a JWT.

Conceptually,

```
User

↓

id = 42

email = alice@example.com

role = admin

↓

JWT

↓

Signed

↓

Access Token
```

The token now represents the authenticated identity.

Notice that

the server isn't storing this token.

It simply creates it,

signs it,

and returns it.

---

# Generating the Refresh Token

Refresh Tokens are different.

Unlike Access Tokens,

they are usually stored by the server.

Conceptually,

```
Generate Random Token

↓

Store In Database

↓

Associate With User

↓

Return To Client
```

Why?

Because Refresh Tokens need to be

- revoked
- rotated
- expired
- managed per device

We'll explore these concepts in detail later.

---

# Response Returned To The Client

A successful login response typically looks like

```json
{
    "access_token": "<jwt>",
    "refresh_token": "<random_token>",
    "expires_in": 900,
    "token_type": "Bearer"
}
```

Some applications instead place one or both tokens in **HttpOnly cookies**.

The storage strategy depends on the client application and security requirements.

We'll compare these approaches in a later chapter.

---

# Where Should Tokens Be Stored?

This is one of the most debated topics in backend engineering.

Possible options include

```
Browser Memory
```

```
HttpOnly Cookies
```

```
Local Storage
```

```
Secure Mobile Storage
```

Each approach has different trade-offs.

Rather than choosing one universally,

the correct decision depends on

- application type
- client platform
- threat model

We'll dedicate an entire chapter to token storage strategies.

---

# Authentication Is Now Complete

At this point,

the user has successfully authenticated.

The client now possesses an Access Token that proves the user's identity.

Every future request follows a much simpler flow.

```
Client

↓

Authorization: Bearer <Access Token>

↓

Authentication Middleware

↓

Verify Token

↓

Attach Authenticated User

↓

Business Logic
```

Notice something important.

The user enters their password only once.

Every request after that relies on the Access Token instead of repeatedly verifying credentials.

This dramatically reduces the work performed by the Authentication Service while providing a seamless user experience.

---

# Design Decisions

A well-designed authentication system should follow these principles.

- Passwords are verified only during login.
- Access Tokens should be short-lived.
- Refresh Tokens should be revocable.
- Access Tokens should never contain sensitive information like passwords.
- Token generation should be handled by a dedicated Authentication or Token Service.
- Authentication logic should remain separate from business logic.

---

# Key Takeaways

- Successful authentication results in token generation, not repeated password verification.
- Access Tokens authenticate requests and should have a short lifetime.
- Refresh Tokens obtain new Access Tokens without requiring the user to log in again.
- Refresh Tokens are typically persisted so they can be revoked and rotated.
- Token generation belongs inside the Authentication Service, keeping authentication concerns isolated from business services.

---

# Authenticating Every Request

At this point, the user has successfully logged in.

The client now possesses an Access Token.

The obvious question becomes

> **How does every future request prove the user's identity?**

Imagine the client wants to fetch their profile.

```http
GET /profile
```

The client attaches the Access Token.

```http
GET /profile

Authorization: Bearer <JWT>
```

The request now reaches your backend.

Notice something.

The request has **not** been authenticated yet.

It merely contains credentials.

Authentication still needs to happen.

---

# High-Level Request Flow

Every authenticated request follows the same lifecycle.

```
                 Client

                   │

 Authorization: Bearer JWT

                   │

                   ▼

            API Gateway

                   │

                   ▼

      Authentication Middleware

                   │

       Extract Access Token

                   │

                   ▼

        Verify JWT Signature

                   │

                   ▼

          Validate Claims

                   │

                   ▼

       Create Auth Context

                   │

                   ▼

        Authorization Layer

                   │

                   ▼

          Business Service

                   │

                   ▼

              Database

                   │

                   ▼

              Response
```

Authentication is only one stage in the request pipeline.

Business logic should never execute before authentication succeeds.

---

# Authentication Middleware

Authentication middleware sits between the incoming request and the application.

Its responsibility is simple.

```
Incoming Request

↓

Is this request authenticated?

↓

Yes

↓

Continue

or

↓

No

↓

Reject
```

The middleware doesn't know anything about

- Orders
- Payments
- Products
- Customers

Its only responsibility is identity verification.

This separation keeps authentication independent from business logic.

---

# Step 1 - Extract the Token

The middleware first checks whether the request contains an Access Token.

Typically,

```
Authorization

↓

Bearer eyJhb...
```

If the header is missing,

authentication immediately fails.

```
401 Unauthorized
```

There is no point continuing.

---

# Step 2 - Verify the Signature

Next,

the JWT signature is verified.

Conceptually,

```
Received JWT

↓

Header

↓

Payload

↓

Signature

↓

Generate Signature Again

↓

Compare

↓

Valid?
```

If the signatures don't match,

the token has either

- been modified
- been forged
- been signed with another key

The request is rejected.

---

# Step 3 - Validate Claims

A valid signature isn't enough.

The middleware also validates the token claims.

Typical checks include

```
Has Token Expired?

↓

exp
```

```
Correct Issuer?

↓

iss
```

```
Correct Audience?

↓

aud
```

```
Token Active?

↓

nbf
```

Only after all validations succeed can the token be trusted.

---

# Step 4 - Build the Authentication Context

Once verification succeeds,

the middleware extracts the user information.

Example

```
JWT Payload

↓

user_id

↓

42

role

↓

admin

email

↓

alice@example.com
```

This information becomes the authenticated identity for the request.

Many frameworks expose this as

```
request.user
```

or

```
current_user
```

or

```
Principal
```

depending on the framework.

Notice something important.

The application never parses the JWT again.

It simply uses the authenticated user attached by the middleware.

---

# Why request.user Matters

Imagine every controller had to verify JWTs manually.

```
Orders

↓

Verify JWT
```

```
Payments

↓

Verify JWT
```

```
Products

↓

Verify JWT
```

```
Users

↓

Verify JWT
```

Every service now contains duplicated authentication logic.

Instead,

authentication happens once.

```
Incoming Request

↓

Authentication Middleware

↓

request.user

↓

Business Logic
```

Business services simply consume the authenticated user.

This is one of the cleanest examples of Separation of Concerns.

---

# Authorization Comes Next

Authentication only answers

> Who is making the request?

Suppose

```
request.user

↓

User ID = 42

Role = Customer
```

Now the application asks another question.

```
Can this customer delete another user's account?
```

That's no longer authentication.

That's authorization.

Conceptually,

```
Authenticate User

↓

Identity Established

↓

Check Permissions

↓

Business Logic
```

Authentication always happens before authorization.

---

# Example Request Flow

Imagine Alice wants to update her profile.

```
PUT /profile
```

The request reaches the backend.

```
Client

↓

Authorization Header

↓

Authentication Middleware

↓

Verify JWT

↓

Extract User

↓

request.user = Alice

↓

Authorization

↓

Allow

↓

Update Profile
```

Now imagine someone sends an invalid JWT.

```
Client

↓

Invalid JWT

↓

Authentication Middleware

↓

Reject

↓

401 Unauthorized
```

The request never reaches the Profile Service.

---

# Why This Architecture Scales

One of the biggest advantages of middleware-based authentication is consistency.

Every service receives the same authenticated context.

```
Orders Service

↓

request.user
```

```
Payments Service

↓

request.user
```

```
Inventory Service

↓

request.user
```

No service needs to understand JWT internals.

They simply trust the Authentication Layer.

This keeps authentication centralized and business services focused on domain logic.

---

# Common Design Mistakes

❌ Verifying JWTs inside every controller.

This leads to duplicated code and inconsistent security.

Authentication should happen once in middleware.

---

❌ Mixing authentication with authorization.

Authentication establishes identity.

Authorization determines whether that identity can perform the requested action.

Treat them as separate responsibilities.

---

❌ Passing raw JWTs throughout the application.

After verification,

convert the token into an authenticated user or security context.

Business logic should work with user information,

not JWT parsing.

---

# Key Takeaways

- Every authenticated request passes through an Authentication Middleware.
- The middleware extracts and verifies the Access Token.
- Signature verification alone is not enough; token claims must also be validated.
- After successful verification, an authenticated context (such as `request.user`) is created.
- Business services should consume the authenticated user rather than parsing JWTs themselves.
- Authentication and authorization are separate stages in the request lifecycle.

---

# Managing Authentication in Production

Issuing an Access Token is only the beginning.

Once users start using your application,

new questions appear.

- What happens when a user logs out?
- What happens if a Refresh Token is stolen?
- How do users stay logged in across multiple devices?
- What happens when a user changes their password?
- How do we revoke access immediately?

These are the problems a production authentication system must solve.

---

# Logout

Many developers assume logout simply means

```
Client

↓

Delete JWT

↓

Done
```

This is only partially correct.

Deleting the Access Token removes it from the client,

but it doesn't invalidate the token itself.

If someone has already stolen that Access Token,

they can continue using it until it expires.

That's why logout is usually centered around the Refresh Token.

---

## Production Logout Flow

```
Client

↓

POST /logout

↓

Authentication Service

↓

Delete Refresh Token

↓

Return Success

↓

Client Deletes Access Token
```

Notice what happened.

The Refresh Token has been invalidated.

The current Access Token may still remain valid for a few minutes,

but once it expires,

the attacker can no longer obtain a new Access Token.

---

# Why We Usually Don't Revoke Access Tokens

A common interview question is

> Why don't we store Access Tokens in the database and revoke them during logout?

Imagine

```
10 Million Users

↓

100 Requests / Second

↓

Database Lookup

↓

Every Request
```

The entire purpose of JWT is to avoid server-side lookups.

If every request required checking whether the Access Token had been revoked,

we would lose the biggest advantage of stateless authentication.

Instead,

production systems usually make Access Tokens

```
Very Short Lived

↓

10-15 Minutes
```

Even if an attacker steals one,

its lifetime is limited.

---

# Refresh Token Rotation

Suppose Refresh Tokens never changed.

```
Refresh Token

↓

Valid For 30 Days
```

Now imagine an attacker steals it.

For the next 30 days,

they can generate new Access Tokens.

That's a serious problem.

Instead,

many production systems rotate Refresh Tokens.

```
Refresh Request

↓

Old Refresh Token

↓

Generate New Refresh Token

↓

Invalidate Old One

↓

Return New Token
```

After every successful refresh,

the old Refresh Token becomes useless.

This significantly reduces the impact of token theft.

---

# Detecting Refresh Token Reuse

Here's where things get interesting.

Suppose

```
Refresh Token A
```

was already rotated.

Later,

the server receives

```
Refresh Token A
```

again.

That should never happen.

```
Refresh Token Used Again

↓

Possible Token Theft

↓

Invalidate All User Sessions

↓

Require Login Again
```

This is known as **Refresh Token Reuse Detection**.

Many modern identity providers implement this mechanism.

---

# Multi-Device Login

Most users don't log in from just one device.

A typical user might have

```
Laptop

Phone

Tablet
```

Each device should have its own Refresh Token.

Conceptually,

```
User

↓

Device A

↓

Refresh Token A
```

```
User

↓

Device B

↓

Refresh Token B
```

```
User

↓

Device C

↓

Refresh Token C
```

This design allows users to log out of one device without affecting the others.

---

# Logging Out of One Device

Suppose the user logs out only from their laptop.

```
Delete Refresh Token A

↓

Phone Still Logged In

↓

Tablet Still Logged In
```

This provides a much better user experience than forcing logout from every device.

---

# Logout From All Devices

Sometimes users choose

```
Logout From All Devices
```

The server simply removes every Refresh Token associated with that user.

```
Refresh Token A

×

Deleted
```

```
Refresh Token B

×

Deleted
```

```
Refresh Token C

×

Deleted
```

Once existing Access Tokens expire,

all devices are logged out.

---

# Password Change

Changing a password is a security-sensitive operation.

Imagine the user's account has been compromised.

If they change their password,

the attacker shouldn't remain logged in.

A common production strategy is

```
Password Changed

↓

Delete All Refresh Tokens

↓

Force Reauthentication

↓

Issue New Tokens
```

This immediately prevents attackers from obtaining new Access Tokens.

---

# Compromised Account Recovery

Suppose unusual activity is detected.

Examples include

- Login from another country
- Impossible travel
- Multiple failed login attempts
- Refresh Token reuse

The Authentication Service may choose to

```
Invalidate Refresh Tokens

↓

Require MFA

↓

Force Password Reset
```

This limits the impact of compromised credentials.

---

# Audit Logging

Authentication systems should maintain an audit trail.

Typical events include

```
User Registered

User Logged In

User Logged Out

Password Changed

Refresh Token Used

Refresh Token Reused

Password Reset

Failed Login Attempt
```

Audit logs are invaluable for

- Security investigations
- Compliance
- Incident response
- User support

Authentication events should always be traceable.

---

# Design Principles

A production authentication system should follow these principles.

- Keep Access Tokens short-lived.
- Persist Refresh Tokens.
- Rotate Refresh Tokens after use.
- Detect Refresh Token reuse.
- Support multiple devices independently.
- Invalidate Refresh Tokens after password changes.
- Record authentication events for auditing.
- Never rely on Access Token revocation as the primary logout mechanism.

---

# Key Takeaways

- Logging out usually invalidates the Refresh Token rather than the Access Token.
- Short-lived Access Tokens reduce the impact of token theft.
- Refresh Token rotation improves security by limiting the usefulness of stolen tokens.
- Supporting multiple devices requires separate Refresh Tokens for each device.
- Password changes should invalidate all active Refresh Tokens.
- Authentication systems should maintain detailed audit logs for security and compliance.

---

# Authentication APIs

An authentication system is ultimately exposed through APIs.

These APIs become the contract between the Authentication Service and every client, including:

- Web Applications
- Mobile Applications
- Internal Services
- Third-party Integrations

A good API should be

- Stateless
- Predictable
- Versionable
- Secure
- Easy to consume

Let's design the APIs that power our authentication system.

---

# Register User

Creates a new user account.

```http
POST /api/v1/auth/register
```

Request

```json
{
    "name": "Alice",
    "email": "alice@example.com",
    "password": "MyStrongPassword@123"
}
```

Processing

```
Validate Request

↓

Email Already Exists?

↓

Hash Password

↓

Store User

↓

Return Success
```

Success Response

```http
201 Created
```

```json
{
    "message": "User registered successfully."
}
```

Possible Errors

```http
400 Bad Request
```

Validation failed.

```http
409 Conflict
```

Email already registered.

---

# Login

Authenticates a user and issues authentication tokens.

```http
POST /api/v1/auth/login
```

Request

```json
{
    "email": "alice@example.com",
    "password": "MyStrongPassword@123"
}
```

Processing

```
Find User

↓

Verify Password

↓

Generate Access Token

↓

Generate Refresh Token

↓

Store Refresh Token

↓

Return Tokens
```

Success Response

```json
{
    "access_token": "...",
    "refresh_token": "...",
    "expires_in": 900,
    "token_type": "Bearer"
}
```

Possible Errors

```http
401 Unauthorized
```

Invalid credentials.

```http
403 Forbidden
```

Account disabled.

---

# Refresh Access Token

Generates a new Access Token using a valid Refresh Token.

```http
POST /api/v1/auth/refresh
```

Request

```json
{
    "refresh_token": "..."
}
```

Processing

```
Validate Refresh Token

↓

Token Revoked?

↓

Rotate Refresh Token

↓

Generate Access Token

↓

Return New Tokens
```

Success Response

```json
{
    "access_token": "...",
    "refresh_token": "...",
    "expires_in": 900
}
```

Possible Errors

```http
401 Unauthorized
```

Refresh Token expired.

---

# Logout

Logs out the current device.

```http
POST /api/v1/auth/logout
```

Request

```http
Authorization: Bearer <Access Token>
```

or

```json
{
    "refresh_token": "..."
}
```

Processing

```
Delete Refresh Token

↓

Return Success
```

Response

```json
{
    "message": "Logged out successfully."
}
```

---

# Logout From All Devices

```http
POST /api/v1/auth/logout-all
```

Processing

```
Delete Every Refresh Token

↓

Return Success
```

This endpoint is commonly used after

- Password Change
- Account Compromise
- Security Reset

---

# Change Password

```http
POST /api/v1/auth/change-password
```

Request

```json
{
    "old_password": "...",
    "new_password": "..."
}
```

Processing

```
Verify Current Password

↓

Hash New Password

↓

Update User

↓

Delete All Refresh Tokens

↓

Return Success
```

Response

```json
{
    "message": "Password updated successfully."
}
```

---

# Forgot Password

```http
POST /api/v1/auth/forgot-password
```

Request

```json
{
    "email": "alice@example.com"
}
```

Processing

```
Generate Reset Token

↓

Send Email

↓

Return Success
```

Notice

We never reveal whether the email exists.

Instead of

```
User Not Found
```

we always return

```
"If the account exists, a password reset email has been sent."
```

This prevents attackers from enumerating valid email addresses.

---

# Reset Password

```http
POST /api/v1/auth/reset-password
```

Request

```json
{
    "reset_token": "...",
    "new_password": "..."
}
```

Processing

```
Verify Reset Token

↓

Hash Password

↓

Update User

↓

Delete Refresh Tokens

↓

Return Success
```

---

# Verify Email

```http
POST /api/v1/auth/verify-email
```

Request

```json
{
    "verification_token": "..."
}
```

Processing

```
Verify Token

↓

Mark Email Verified

↓

Return Success
```

---

# Get Current User

Very common endpoint.

```http
GET /api/v1/users/me
```

Processing

```
Authentication Middleware

↓

request.user

↓

Fetch User

↓

Return Profile
```

Response

```json
{
    "id": 42,
    "name": "Alice",
    "email": "alice@example.com",
    "roles": [
        "ADMIN"
    ]
}
```

---

# Common HTTP Status Codes

| Status Code | Meaning |
|-------------|---------|
| 200 | Request successful |
| 201 | Resource created |
| 204 | Success with no response body |
| 400 | Validation failed |
| 401 | Authentication failed |
| 403 | Authenticated but not authorized |
| 404 | Resource not found |
| 409 | Resource already exists |
| 429 | Too many requests |
| 500 | Internal server error |

---

# Authentication API Design Principles

A production-grade authentication API should follow these principles.

- Never expose password hashes.
- Never expose internal user IDs unnecessarily.
- Use appropriate HTTP status codes.
- Return generic authentication errors to avoid leaking information.
- Version authentication APIs.
- Keep endpoints focused on a single responsibility.
- Make refresh and logout operations idempotent where possible.
- Rate-limit sensitive endpoints such as login and password reset.

---

# Key Takeaways

- Authentication is exposed through a small set of well-defined APIs.
- Each endpoint should have a single responsibility.
- Security extends beyond token generation to API behavior, error handling, and rate limiting.
- Consistent API contracts make authentication easier to integrate across multiple clients and services.

---

# Complete Production Authentication Architecture

At this point, we've designed every individual building block.

Let's put everything together into a production-ready authentication system.

This is the architecture you would explain in a Senior or Staff Engineer interview.

---

# High-Level Architecture (HLD)

```
                                    Internet
                                        │
                                        ▼
                               Load Balancer / CDN
                                        │
                                        ▼
                                  API Gateway
                                        │
                     ┌──────────────────┴──────────────────┐
                     │                                     │
                     ▼                                     ▼
             Public Endpoints                      Protected Endpoints
        (/login, /register, ...)                      (/orders, /profile)
                     │                                     │
                     └──────────────┬──────────────────────┘
                                    ▼
                        Authentication Middleware
                                    │
                        Verify Access Token (JWT)
                                    │
                                    ▼
                         Build Authentication Context
                            (request.user / Principal)
                                    │
                                    ▼
                        Authorization Layer (RBAC/ABAC)
                                    │
                                    ▼
                            Business Services
             ┌──────────────┬──────────────┬──────────────┐
             ▼              ▼              ▼
        Order Service  User Service  Payment Service
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                     Authentication Service
              ┌─────────────┼────────────────────┐
              ▼             ▼                    ▼
      User Repository   Token Manager    Password Manager
              │             │                    │
              ▼             ▼                    ▼
        PostgreSQL     JWT Signing Key      bcrypt / Argon2
```

---

# Responsibility of Each Component

## Client

Responsible for

- Sending credentials during login
- Storing authentication tokens
- Attaching Access Tokens to authenticated requests
- Requesting new Access Tokens using Refresh Tokens

The client should never perform authentication itself.

---

## API Gateway

Acts as the entry point to the backend.

Responsibilities

- Routing
- Rate limiting
- TLS termination
- Authentication middleware (optional)
- Request logging

In microservice architectures,

JWT verification is often performed here before forwarding the request.

---

## Authentication Middleware

Responsible only for authentication.

```
Incoming Request

↓

Extract JWT

↓

Verify Signature

↓

Validate Claims

↓

Create request.user

↓

Continue
```

If authentication fails,

the request never reaches the application.

---

## Authorization Layer

Authentication answers

```
Who are you?
```

Authorization answers

```
What are you allowed to do?
```

Examples

```
Customer

↓

Read Own Orders

✓
```

```
Customer

↓

Delete Another User

✗
```

Keep authentication and authorization as separate concerns.

---

## Authentication Service

Owns every authentication-related operation.

Examples

- Register User
- Login
- Refresh Tokens
- Logout
- Password Reset
- Email Verification

Business services should never generate JWTs directly.

---

## Business Services

These services focus only on domain logic.

Examples

- Orders
- Inventory
- Payments
- Products

They receive an already authenticated user.

```
request.user

↓

Business Logic
```

They should never parse JWTs themselves.

---

# Request Lifecycle

Every authenticated request follows the same lifecycle.

```
Client

↓

Authorization: Bearer JWT

↓

API Gateway

↓

Authentication Middleware

↓

Verify JWT

↓

request.user

↓

Authorization

↓

Business Logic

↓

Database

↓

Response
```

Notice

Authentication happens once.

Business logic never performs authentication again.

---

# Complete Login Sequence

```
User

↓

POST /login

↓

Authentication Service

↓

Find User

↓

Verify Password

↓

Generate Access Token

↓

Generate Refresh Token

↓

Persist Refresh Token

↓

Return Tokens

↓

Client Stores Tokens
```

---

# Refresh Token Flow

```
Access Token Expired

↓

POST /refresh

↓

Validate Refresh Token

↓

Generate New Access Token

↓

Rotate Refresh Token

↓

Persist New Refresh Token

↓

Return Tokens
```

---

# Logout Flow

```
POST /logout

↓

Delete Refresh Token

↓

Client Deletes Access Token

↓

Done
```

---

# Password Reset Flow

```
Forgot Password

↓

Generate Reset Token

↓

Email User

↓

Reset Password

↓

Invalidate Refresh Tokens

↓

Require Login Again
```

---

# Design Principles

A production authentication system should follow these principles.

## Single Responsibility

Authentication belongs to the Authentication Service.

Authorization belongs to the Authorization Layer.

Business logic belongs to business services.

---

## Stateless Authentication

Use Access Tokens to avoid database lookups on every request.

---

## Stateful Refresh Tokens

Store Refresh Tokens so they can be

- revoked
- rotated
- expired
- managed per device

---

## Short-lived Access Tokens

Access Tokens should expire quickly.

Typical values

```
10-15 Minutes
```

---

## Long-lived Refresh Tokens

Refresh Tokens typically live longer.

Examples

```
7 Days

30 Days

90 Days
```

depending on business requirements.

---

## Principle of Least Privilege

JWTs should contain only the information required for authentication.

Avoid placing

- passwords
- permissions that change frequently
- sensitive business data

inside tokens.

---

# Common Production Enhancements

As systems grow,

authentication often integrates with additional services.

Examples

```
Redis

↓

Rate Limiting

↓

OTP Storage

↓

Temporary Caches
```

```
Kafka

↓

UserLoggedIn Event

↓

Audit Pipelines

↓

Analytics
```

```
Email Service

↓

Verification Emails

↓

Password Reset Emails
```

```
Monitoring

↓

Login Failures

↓

Token Refresh Rate

↓

Authentication Latency
```

These services are not required initially,

but become common as systems scale.

---

# Common Interview Questions

### Why are Access Tokens stateless but Refresh Tokens stateful?

Because Access Tokens are optimized for fast request authentication without database lookups.

Refresh Tokens require server-side state so they can be revoked, rotated, and managed securely.

---

### Why not revoke Access Tokens during logout?

Doing so would require checking every Access Token against server-side storage on every request, defeating the purpose of stateless authentication.

---

### Why separate authentication from authorization?

Authentication establishes identity.

Authorization determines permissions.

Keeping them separate simplifies the design and improves maintainability.

---

### Should every microservice verify JWTs?

It depends on the architecture.

Some systems centralize verification at the API Gateway.

Others allow each service to verify JWTs independently using a shared public key.

The choice depends on trust boundaries and deployment architecture.

---

# Key Takeaways

- Authentication is a complete subsystem, not just JWT generation.
- Authentication should happen before business logic.
- Business services should receive an authenticated user rather than parsing JWTs.
- Access Tokens optimize request authentication.
- Refresh Tokens manage long-lived sessions securely.
- Authentication and authorization should remain separate responsibilities.
- A well-designed authentication system scales by keeping responsibilities clearly separated.
