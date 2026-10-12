# Cookies

## Prerequisites

Before reading this chapter, you should understand:

- Identity & Authentication
- Sessions

---

# Why Do We Need Cookies?

Imagine you've built an e-commerce application.

A user logs in.

```http
POST /login
```

The server verifies the username and password.

After successful authentication, the server creates a session.

Conceptually,

```
User

↓

Authenticated

↓

Create Session

↓

Session ID

↓

abc123xyz
```

Now the user clicks on another page.

```http
GET /profile
```

A few seconds later,

another request arrives.

```http
GET /orders
```

Then another.

```http
POST /checkout
```

Here's the obvious question.

**How does the server know that all of these requests belong to the same user?**

The session exists.

The Session ID exists.

But where is that Session ID stored?

Who remembers it?

Who sends it back with every request?

The frontend developer isn't manually attaching the Session ID to every HTTP request.

The browser does it automatically.

That's exactly why cookies exist.

---

# The Core Idea

A cookie is simply a small piece of data that the server asks the browser to store.

Later,

whenever the browser sends another request to the same website,

it automatically includes that data.

Conceptually,

```
Server

↓

Store This Value

↓

Browser Stores It

↓

Future Requests

↓

Automatically Send It Back
```

That's the entire idea behind cookies.

Notice something important.

Cookies don't authenticate users.

Cookies don't authorize users.

Cookies don't create sessions.

A cookie is simply a transport mechanism.

Its job is to carry small pieces of information between the browser and the server.

---

# What Can Cookies Store?

Many people think cookies are only used for authentication.

That's not true.

Cookies can store almost any small piece of client-related information.

For example,

```
Session ID

↓

abc123
```

or

```
Language

↓

English
```

or

```
Theme

↓

Dark
```

or

```
Currency

↓

INR
```

The browser doesn't care what the value means.

It simply stores it and sends it back according to the cookie's rules.

---

# Creating a Cookie

Let's see what actually happens.

Alice logs in.

```http
POST /login

{
    "username": "alice",
    "password": "secret"
}
```

The server verifies the credentials.

It creates a session.

```
Session ID

↓

abc123
```

Now the server needs the browser to remember this Session ID.

It doesn't send it inside the JSON response.

Instead,

it uses a special HTTP response header.

```http
HTTP/1.1 200 OK

Set-Cookie:

session_id=abc123
```

Notice something interesting.

The response body might simply be

```json
{
    "message": "Login Successful"
}
```

The Session ID isn't part of the response body.

It's sent through the **Set-Cookie** header.

This is the browser's signal to store a cookie.

---

# Browser Stores the Cookie

When the browser receives

```http
Set-Cookie:

session_id=abc123
```

it stores it in its cookie storage.

Conceptually,

```
Browser

Cookies

────────────────────────────

session_id

↓

abc123
```

Every browser maintains its own cookie storage.

Chrome,

Firefox,

Safari,

Edge,

all manage cookies internally.

The server no longer needs to tell the browser about this cookie again.

The browser remembers it.

---

# Future Requests

Now Alice clicks

```http
GET /profile
```

This time,

something interesting happens.

Before sending the request,

the browser checks

> "Do I have any cookies that belong to this website?"

It finds

```
session_id

↓

abc123
```

The browser automatically adds another HTTP header.

```http
GET /profile

Cookie:

session_id=abc123
```

Notice something important.

The frontend developer usually doesn't write

```javascript
headers.Cookie = ...
```

or

```javascript
fetch(...)

{
    Cookie: ...
}
```

The browser handles this automatically.

As long as the cookie matches the request's rules,

it is included automatically.

This is one of the reasons cookies are so convenient.

---

# Complete HTTP Flow

The entire process looks like this.

```
                    Login Request

                          │

                          ▼

              POST /login

      Username + Password

                          │

                          ▼

             Server Verifies User

                          │

                          ▼

              Create Session

                          │

                          ▼

           Session ID = abc123

                          │

                          ▼

HTTP Response

Set-Cookie:

session_id=abc123

                          │

                          ▼

            Browser Stores Cookie

──────────────────────────────────────────────

              Future Request

                          │

                          ▼

               GET /profile

                          │

                          ▼

Browser Automatically Adds

Cookie:

session_id=abc123

                          │

                          ▼

            Server Reads Cookie

                          │

                          ▼

          Lookup Session Store

                          │

                          ▼

         User Successfully Identified
```

At this point,

the browser has done its job.

The server now needs to read the cookie,

extract the Session ID,

look up the corresponding session,

and identify the user.

---

# How Does the Server Read Cookies?

When the browser sends a request,

it automatically includes the matching cookies inside the HTTP request.

```http
GET /profile HTTP/1.1

Host: example.com

Cookie:
session_id=abc123;
theme=dark;
language=en
```

Notice that all cookies are sent using a single HTTP header.

The server simply reads this header.

Conceptually,

```
Incoming Request

↓

Cookie Header

↓

session_id=abc123

↓

Find Session

↓

Identify User
```

The browser's job ends after sending the cookie.

Everything that happens after that is handled by the server.

---

# Reading Cookies in Python

Different frameworks provide different APIs,

but internally they're all doing the same thing.

FastAPI

```python
from fastapi import Cookie

@app.get("/profile")
def profile(session_id: str = Cookie()):

    print(session_id)
```

Flask

```python
from flask import request

session_id = request.cookies.get("session_id")
```

Django

```python
session_id = request.COOKIES.get("session_id")
```

Regardless of the framework,

the server is simply reading the value from the `Cookie` request header.

---

# Multiple Cookies

A browser can store many cookies for the same website.

For example,

```
Browser

Cookies

──────────────────────────

session_id

↓

abc123


theme

↓

dark


language

↓

en


currency

↓

INR
```

When a request is sent,

the browser combines them into a single header.

```http
Cookie:

session_id=abc123;

theme=dark;

language=en;

currency=INR
```

The server can read whichever cookies it needs.

---

# Does the Browser Send Every Cookie?

No.

This is a common misconception.

Imagine you've visited

```
amazon.com
```

and

```
github.com
```

Your browser stores cookies for both websites.

```
amazon.com

↓

session_id


github.com

↓

session_id
```

Now you visit

```
github.com
```

Will the browser send Amazon's cookies?

Absolutely not.

The browser only sends cookies that belong to the current website.

```
Browser

↓

github.com Request

↓

Send GitHub Cookies Only
```

This behavior is one of the fundamental security guarantees provided by browsers.

---

# Cookie Domain

Every cookie belongs to a domain.

Suppose the server returns

```http
Set-Cookie:

session_id=abc123;

Domain=example.com
```

Now the browser knows

```
This cookie belongs to

example.com
```

Whenever the user visits

```
example.com
```

or

```
api.example.com
```

the browser may send that cookie, depending on the domain rules.

However,

if the user visits

```
google.com
```

the cookie is not sent.

Conceptually,

```
Cookie

↓

example.com

↓

Only Requests Matching

example.com
```

---

# Cookie Path

Cookies can also be limited to specific URL paths.

Suppose

```http
Set-Cookie:

admin_session=xyz;

Path=/admin
```

Now consider these requests.

```
GET /admin/users
```

Cookie sent.

```
GET /admin/settings
```

Cookie sent.

```
GET /products
```

Cookie not sent.

The browser checks the request path before deciding whether the cookie should be included.

This allows applications to scope cookies to particular areas of a website.

---

# Cookie Matching

Before sending a cookie,

the browser performs several checks.

Conceptually,

```
Request

↓

Does Domain Match?

↓

Does Path Match?

↓

Has Cookie Expired?

↓

Is HTTPS Required?

↓

Send Cookie
```

Only if all conditions are satisfied does the browser include the cookie in the request.

The application developer usually doesn't have to implement this logic.

The browser does it automatically.

---

# Session Cookies vs Persistent Cookies

Not all cookies live for the same amount of time.

There are two common types.

## Session Cookies

These cookies exist only while the browser session is active.

```
Browser Open

↓

Cookie Exists

↓

Browser Closed

↓

Cookie Removed
```

If the browser is closed,

the cookie disappears.

They are commonly used for temporary login sessions.

---

## Persistent Cookies

Persistent cookies have an expiration time.

For example,

```http
Set-Cookie:

theme=dark;

Max-Age=2592000
```

This cookie remains stored even if the browser is restarted.

```
Today

↓

Cookie Created

↓

Tomorrow

↓

Still Exists

↓

30 Days Later

↓

Browser Deletes Cookie
```

Persistent cookies are commonly used for

- Remember Me
- Theme
- Language
- User Preferences

---

# Cookie Lifecycle

Putting everything together,

a cookie follows this lifecycle.

```
Server Creates Cookie

        │

        ▼

Browser Stores Cookie

        │

        ▼

Browser Evaluates Rules

(Domain, Path, Expiry...)

        │

        ▼

Matching Request?

      │

 Yes │ No

      ▼

Send Cookie

      │

      ▼

Server Reads Cookie

      │

      ▼

Cookie Updated

or

Cookie Deleted
```

The browser acts like a small cookie manager,

constantly deciding

whether each stored cookie should accompany a particular request.

---

# Cookie Security

So far we've learned that cookies are simply small pieces of data stored by the browser and automatically sent back to the server.

Naturally, another question arises.

> If cookies are sent automatically with every request, couldn't an attacker steal or misuse them?

Yes.

That's why modern browsers provide several security mechanisms to control how cookies behave.

Understanding these attributes is essential for building secure web applications.

---

# HttpOnly

Imagine your application stores the Session ID inside a cookie.

```
session_id

↓

abc123
```

Now suppose an attacker successfully injects JavaScript into your page using a Cross-Site Scripting (XSS) vulnerability.

Without any protection,

the malicious script could execute

```javascript
document.cookie
```

and steal the Session ID.

```
Browser

↓

document.cookie

↓

session_id=abc123

↓

Attacker
```

Now the attacker can impersonate the user.

To prevent this,

the server marks the cookie as

```http
Set-Cookie:

session_id=abc123;

HttpOnly
```

Now,

even though the browser continues sending the cookie with every request,

JavaScript can no longer read it.

```
Browser

↓

document.cookie

↓

Blocked
```

This significantly reduces the impact of XSS attacks.

> **Best Practice:** Authentication cookies should almost always use `HttpOnly`.

---

# Secure

Cookies travel over HTTP requests.

If your application is accessible over plain HTTP,

an attacker on the same network could potentially intercept the traffic.

To prevent the browser from sending cookies over unencrypted connections,

use

```http
Secure
```

Example

```http
Set-Cookie:

session_id=abc123;

Secure
```

Now the browser behaves like this.

```
HTTPS

↓

Send Cookie



HTTP

↓

Don't Send Cookie
```

Notice something.

The browser enforces this.

Your application doesn't have to write any additional code.

> **Best Practice:** Authentication cookies should always use `Secure` in production.

---

# SameSite

Cookies are automatically sent with requests.

Normally that's convenient.

Sometimes it's dangerous.

Imagine you're logged into your bank.

In another browser tab,

you accidentally visit a malicious website.

That website secretly submits

```http
POST /transfer-money
```

to your bank.

Since the request is going to your bank,

the browser automatically includes your session cookie.

```
Malicious Website

↓

POST

↓

Bank

↓

Cookie Automatically Added
```

The bank receives

```
Valid Session

↓

Looks Legitimate
```

This attack is called

```
Cross-Site Request Forgery (CSRF)
```

To reduce this risk,

browsers support

```
SameSite
```

---

## SameSite=Strict

```
Set-Cookie:

SameSite=Strict
```

The browser sends the cookie only when navigating within the same site.

```
example.com

↓

example.com

↓

Cookie Sent
```

```
evil.com

↓

example.com

↓

Cookie Not Sent
```

This provides the strongest CSRF protection.

---

## SameSite=Lax

```
SameSite=Lax
```

This is a balanced approach.

Cookies are sent for normal navigation,

but blocked for many cross-site requests that are commonly used in CSRF attacks.

Many browsers use **Lax** as the default behavior.

---

## SameSite=None

```
SameSite=None
```

The cookie is allowed in cross-site requests.

This is required for certain scenarios,

such as third-party authentication providers.

However,

modern browsers require

```
Secure
```

whenever

```
SameSite=None
```

is used.

---

# Cookie Attributes at a Glance

| Attribute | Purpose |
|-----------|---------|
| HttpOnly | Prevent JavaScript from reading the cookie |
| Secure | Send cookie only over HTTPS |
| SameSite | Control when cookies are sent with cross-site requests |
| Domain | Restrict which domains receive the cookie |
| Path | Restrict which URLs receive the cookie |
| Max-Age / Expires | Control cookie lifetime |

---

# Signed Cookies

One important question remains.

What's stopping a user from opening DevTools and changing

```
role=user
```

to

```
role=admin
```

Nothing.

Unless the application protects it.

A common approach is to **sign** the cookie.

```
Cookie Data

↓

Cryptographic Signature

↓

Browser
```

When the browser sends the cookie back,

the server verifies the signature.

```
Cookie Modified?

↓

Signature Invalid

↓

Reject Request
```

Notice something important.

Signing does **not** hide the data.

It simply detects tampering.

---

# Encrypted Cookies

Sometimes the cookie itself contains sensitive information.

Instead of only signing it,

the application encrypts it.

```
Sensitive Data

↓

Encrypt

↓

Cookie
```

Now,

even if someone opens Developer Tools,

they cannot understand the cookie contents without the encryption key.

---

# Signed vs Encrypted

```
Signed

↓

Can Read

Cannot Modify



Encrypted

↓

Cannot Read

Cannot Modify
```

Many production systems use both.

---

# Common Misconceptions

### Cookies are not encrypted by default.

False.

Cookies are plain text unless the application encrypts them.

---

### HttpOnly makes cookies secure.

False.

It protects against JavaScript access,

not every attack.

---

### Secure encrypts cookies.

False.

HTTPS encrypts the network traffic.

The Secure flag simply tells the browser

*"Never send this cookie over HTTP."*

---

### Cookies are only for authentication.

False.

Cookies can store

- User Preferences
- Language
- Shopping Cart IDs
- Feature Flags
- Analytics Identifiers

Authentication is just one use case.

---

# Production Best Practices

For authentication cookies,

a typical production configuration is

```http
Set-Cookie:

session_id=abc123;

HttpOnly;

Secure;

SameSite=Lax
```

Additionally,

- Always use HTTPS.
- Rotate Session IDs after login.
- Expire sessions after inactivity.
- Invalidate sessions during logout.
- Store only a Session ID inside the cookie.
- Keep sensitive user information on the server.

---

# Common Interview Questions

### What is the purpose of HttpOnly?

It prevents JavaScript from accessing the cookie, helping mitigate the impact of XSS attacks while still allowing the browser to send the cookie automatically.

---

### Why do we use Secure?

It instructs the browser to send the cookie only over HTTPS, reducing the risk of interception on unencrypted connections.

---

### What problem does SameSite solve?

It helps mitigate CSRF attacks by controlling when browsers include cookies with cross-site requests.

---

### Can users modify cookies?

Yes.

Cookies stored in the browser can be modified unless the application protects them using signatures or validates them appropriately.

---

### What's the difference between signed and encrypted cookies?

Signed cookies protect integrity by detecting tampering.

Encrypted cookies protect confidentiality by hiding the contents.

Many applications use both.

---

# Common Interview Mistakes

❌ Saying cookies are encrypted by default.

✔ Cookies are plain text unless the application encrypts them.

---

❌ Saying HttpOnly encrypts cookies.

✔ HttpOnly only prevents JavaScript from reading them.

---

❌ Assuming Secure encrypts cookies.

✔ HTTPS encrypts traffic. Secure tells the browser not to send cookies over HTTP.

---

❌ Storing sensitive user information directly in cookies.

✔ Store only an identifier whenever possible and keep sensitive data on the server.

---

# Key Takeaways

- Cookies are a browser storage and transport mechanism.
- Browsers automatically send matching cookies with requests.
- `HttpOnly` protects against JavaScript access.
- `Secure` ensures cookies are sent only over HTTPS.
- `SameSite` helps mitigate CSRF attacks.
- Signed cookies detect tampering.
- Encrypted cookies protect confidentiality.
- For authentication, cookies typically store only a Session ID while the server stores the actual session data.