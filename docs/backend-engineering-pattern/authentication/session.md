# Sessions

## Why Do We Need Sessions?

In the previous chapter, we learned that after a user is authenticated, the server somehow needs to remember who they are.

Let's think about what actually happens.

Alice logs into an application.

```
POST /login
```

She enters

- Username
- Password

The server verifies her credentials.

Great.

Now Alice opens another page.

```
GET /profile
```

How does the server know this request also belongs to Alice?

HTTP doesn't remember previous requests.

Every HTTP request is completely independent.

```
Request 1

↓

Server

↓

Response



Request 2

↓

Server

↓

Response
```

There is no built-in concept of

> "This request belongs to the same user."

Without some additional mechanism,

Alice would have to send her username and password with **every request**.

Clearly that's not practical.

So the server needs a way to remember that Alice has already logged in.

That's exactly what a session solves.

---

## The Core Idea

Instead of asking Alice to prove her identity on every request,

the server remembers that she has already authenticated.

Conceptually,

```
Login Request

↓

Verify Password

↓

Create Session

↓

Store Session

↓

Return Session ID
```

Every future request automatically includes the session identifier as a cookie, allowing the server to retrieve the associated session and identify the user.

The server looks it up,

finds Alice,

and continues processing the request.

---

## How a Session Works

Suppose Alice logs in.

```
Client

↓

POST /login

↓

Username + Password
```

The server verifies the credentials.

Then something new happens.

```
Server

↓

Generate Session ID

↓

Store Session

↓

Return Session ID
```

The server might store something like

```
Session ID

↓

a8f91d2c...

↓

User ID = 42

Role = Admin

Expires = 8 PM
```

Notice something important.

The browser never receives Alice's identity.

It only receives the session identifier.

---

## Session Creation in Practice

Let's see what actually happens at the HTTP level.

### Step 1: User Logs In

The browser sends the user's credentials.

```http
POST /login HTTP/1.1

{
    "username": "alice",
    "password": "secret"
}
```

---

### Step 2: Server Verifies Credentials

The server validates the username and password against the database.

If the credentials are valid,

the server creates a new session.

A session identifier should be cryptographically secure and impossible to guess.

In Python, this can be generated using the `secrets` module.

```python
import secrets

session_id = secrets.token_hex(32)

print(session_id)
```

Example output

```
f8c50d61dc7c2c4b8b7d9d8d6a0c4...
```

Notice that the session ID contains **no user information**.

It is simply a random identifier.

---

### Step 3: Store the Session

The server stores the session internally.

For example,

```python
session_store = {
    "f8c50d61dc7...": {
        "user_id": 42,
        "username": "alice",
        "role": "admin"
    }
}
```

Conceptually,

```
Session ID

↓

User Information
```

Only the server has access to this data.

---

### Step 4: Return the Session ID

Instead of returning the user's identity,

the server sends the session ID using the `Set-Cookie` response header.

```http
HTTP/1.1 200 OK

Set-Cookie:
session_id=f8c50d61dc7...;
HttpOnly;
Secure;
SameSite=Lax
```

The browser automatically stores this cookie.

```
Browser

Cookies

----------------------

session_id

↓

f8c50d61dc7...
```

---

### Step 5: Future Requests

Whenever the browser makes another request to the same website,

it automatically includes the cookie.

```http
GET /profile HTTP/1.1

Cookie:
session_id=f8c50d61dc7...
```

Notice something important.

The frontend developer usually doesn't add this cookie manually.

The browser handles it automatically.

---

### Step 6: Server Authenticates the User

The server extracts the session ID from the incoming cookie.

```
Cookie

↓

Session ID

↓

Lookup Session Store

↓

User Found

↓

Request Authenticated
```

If the session exists,

the request proceeds.

Otherwise,

the server returns

```
401 Unauthorized
```

---

## Request Flow

After login,

future requests look like this.

```
                Browser

                   │

     Session ID = a8f91d2c

                   │

                   ▼

               Server

                   │

          Lookup Session ID

                   │

                   ▼

             Session Store

                   │

         User ID = 42

         Role = Admin

                   │

                   ▼

          Execute Request
```

The session ID is simply a key.

The actual user information remains on the server.

---

## What Does the Server Store?

A session can contain anything the application needs.

For example,

```
Session

├── User ID
├── Username
├── Roles
├── Permissions
├── Login Time
├── Expiry Time
└── CSRF Token
```

Applications choose what to store.

The important point is that **the server owns the session data**.

---

## Where Are Sessions Stored?

This depends on the application.

Small applications often keep sessions in memory.

```
Application

↓

Memory

↓

Sessions
```

Larger applications usually use a shared store.

```
Application 1

Application 2

Application 3

        │

        ▼

      Redis

        │

     Sessions
```

Using a shared session store allows multiple application servers to authenticate the same user.

---

## Why Not Store Everything in the Browser?

Imagine sending this with every request.

```
User ID

Roles

Permissions

Email

Account Status
```

The client could modify it.

Instead,

the browser only receives

```
Session ID

↓

f81ac42...
```

The actual user information never leaves the server.

That's one of the biggest advantages of session-based authentication.

---

## Session Lifecycle

```
User Logs In

        │

        ▼

Credentials Verified

        │

        ▼

Create Session

        │

        ▼

Store Session

        │

        ▼

Return Session ID

        │

        ▼

Subsequent Requests

        │

        ▼

Lookup Session

        │

        ▼

User Logs Out

        │

        ▼

Delete Session
```

Logging out is simple.

The server removes the session.

The next request using that session ID is rejected.

---

## Advantages

Sessions work well because

- Sensitive user information stays on the server.
- Logging out is straightforward.
- Sessions can be invalidated immediately.
- Permissions can be changed without issuing new tokens.

This makes sessions a popular choice for traditional web applications.

---

## Challenges

Sessions also introduce new challenges.

### The server must remember every logged-in user.

```
1 User

↓

1 Session
```

```
1 Million Users

↓

1 Million Sessions
```

Memory usage grows with the number of active users.

---

### Scaling

Imagine two application servers.

```
          Load Balancer

           │        │

           ▼        ▼

      Server A   Server B
```

Alice logs into Server A.

The session exists only there.

Now the next request reaches Server B.

Server B doesn't know who Alice is.

One solution is

**Sticky Sessions**

or

a shared session store like Redis.

---

### Session Expiration

Sessions shouldn't live forever.

Eventually,

they expire.

```
Session Created

↓

Active

↓

Expired

↓

Deleted
```

Applications typically use idle timeouts, absolute expiration times, or both.

---

## Real-World Example

Imagine you're using Amazon.

You log in once.

For the next several hours,

you browse products,

add items to your cart,

place orders,

and update your profile.

You aren't typing your password every few minutes.

Amazon remembers you by using a session (or another persistent authentication mechanism that serves the same purpose).

The important idea is the same:

the server recognizes that you've already authenticated.

---

## What's Next?

One question should naturally come to mind.

Sessions require the server to remember every logged-in user.

What happens when we have

- hundreds of servers,
- millions of users,
- microservices,
- global deployments?

Do all servers need to share session state?

This limitation led to a different approach:

**Stateless Authentication**, which we'll explore through JWT.

---

## Common Interview Questions

### Why do we need sessions?

HTTP is stateless. Sessions allow the server to remember that a user has already authenticated across multiple requests.

---

### What does a session store?

A session typically stores information about the authenticated user, such as their user ID, roles, permissions, login time, and expiration time. The exact contents depend on the application's needs.

---

### Where are sessions stored?

Sessions may be stored in application memory, a database, or a shared store such as Redis. Distributed applications commonly use Redis so multiple servers can access the same session.

---

### Why is only the session ID sent to the client?

The session ID acts as a reference to the server-side session. Keeping the actual user data on the server prevents clients from modifying sensitive authentication information.

---

### How does logout work with sessions?

Logging out simply removes the session from the server. Any future request using that session ID will fail because the server no longer recognizes it.

---

### Why are sessions called stateful?

Because the server maintains state for every authenticated user. The server must remember active sessions between requests.

---

## Common Interview Mistakes

❌ Thinking the browser stores the user's identity.

✔ The browser stores only a session identifier. The user information remains on the server.

---

❌ Assuming sessions don't scale.

✔ Sessions scale well when paired with shared session stores like Redis or other distributed storage solutions.

---

❌ Assuming sessions are insecure.

✔ Properly implemented sessions are highly secure. Security depends on practices such as secure cookies, HTTPS, session expiration, and protection against session hijacking.

---

## Key Takeaways

- HTTP is stateless, so the server needs a mechanism to remember authenticated users.
- A session is server-side state associated with an authenticated user.
- The client stores only a session ID, while the server stores the session data.
- Logging out removes the server-side session.
- Sessions simplify permission updates and revocation but require server-side storage and coordination in distributed systems.