# Django Interview Handbook

> This handbook is not meant to teach Django from scratch.
>
> It's meant to teach you how experienced backend engineers think about Django during interviews.
>
> Every answer is written from the perspective of someone who has designed, built, deployed, debugged, and scaled Django applications in production.
>
> The focus is not on memorizing APIs.
>
> The focus is understanding why Django works the way it does, the trade-offs behind its design, and the kinds of production problems you'll eventually encounter.

---

# Prerequisites

Before reading this handbook, you should understand:

- Python
- OOP
- SQL
- HTTP
- REST APIs
- Authentication & Authorization

---

# How To Use This Handbook

Most interview guides teach you **what Django is.**

This handbook teaches you **how to think about Django.**

Every interview answer follows roughly the same philosophy.

```
Problem

↓

Why does this exist?

↓

How Django solves it

↓

Production Perspective

↓

Trade-offs

↓

Possible Follow-up Questions
```

If you understand the problem,

the implementation becomes much easier to remember.

---

# Django Architecture

## Interview Question

**What is Django? Why would you choose Django over other frameworks?**

---

### Answer

I usually describe Django as a batteries-included backend framework.

Most frameworks give you a web framework.

Django gives you an ecosystem.

Out of the box you get things like

- ORM
- Authentication
- Admin Panel
- Migrations
- Middleware
- Forms
- Security Features
- Session Management
- Caching Support

Instead of choosing ten different libraries,

Django already provides opinionated solutions that work well together.

That's probably its biggest strength.

For small and medium-sized teams,

this dramatically increases development speed because everyone follows similar conventions.

---

Another reason I like Django is that it encourages consistency.

If ten developers join the same project,

the project structure usually looks familiar.

Models live in `models.py`.

Views live in `views.py`.

URLs are routed through `urls.py`.

Migrations are managed consistently.

That consistency becomes valuable as teams grow.

---

Having said that,

I don't think Django is the right framework for every problem.

If I'm building a CRUD-heavy application,

an admin dashboard,

an internal business application,

or an API backend,

Django is usually one of my first choices.

If I'm building an extremely lightweight microservice that exposes only a couple of APIs,

I might choose FastAPI instead because it has a smaller footprint and excellent async support.

Like most engineering decisions,

it's about choosing the right tool rather than finding the "best" framework.

---

# Django's Philosophy

One thing that separates Django from many frameworks is that it is intentionally opinionated.

Instead of asking the developer to assemble dozens of libraries,

Django says

> "Here's the recommended way to build web applications."

Some engineers dislike that.

Personally,

I think it's one of Django's biggest strengths.

When every project follows similar conventions,

developers spend less time debating architecture and more time solving business problems.

---

# MVT vs MVC

## Interview Question

**Django says it follows MVT instead of MVC. What's the difference?**

---

### Answer

Honestly,

I don't spend much time thinking about MVT versus MVC.

In practice,

they're solving the same problem.

The naming is just slightly different.

If someone comes from Spring Boot or ASP.NET,

they'll usually think in terms of MVC.

Django simply renamed one of the components.

```
MVC

Model

View

Controller
```

becomes

```
MVT

Model

View

Template
```

The interesting part is where the controller went.

In Django,

there isn't a single Controller class.

Its responsibilities are distributed across

- URL Dispatcher
- Middleware
- Views

So instead of having one central controller,

Django spreads those responsibilities across multiple components.

From an engineering perspective,

I don't think the naming matters very much.

Understanding the request lifecycle is much more important.

---

# Django Request Lifecycle

This is probably the single most important Django interview question.

Almost every senior Django interview eventually asks some variation of

> Walk me through what happens when a request reaches your Django application.

Rather than memorizing the flow,

I prefer understanding it.

Imagine someone opens

```
GET /users/42
```

The request doesn't immediately reach your Django view.

There are several components involved before your business logic even executes.

```
Client

↓

Nginx

↓

Gunicorn / Uvicorn

↓

WSGI / ASGI

↓

Django Middleware

↓

URL Resolver

↓

View

↓

Business Logic

↓

ORM

↓

Database

↓

Response

↓

Middleware

↓

Client
```

If you've ever debugged production systems,

this flow becomes incredibly useful because performance issues can occur at almost every stage.

For example,

a slow request isn't always caused by a slow database.

Sometimes it's

- middleware
- authentication
- serialization
- network latency
- external APIs

Understanding the request lifecycle helps narrow down where the bottleneck actually is.

We'll now walk through each component in detail.

---

# Nginx

The browser doesn't usually talk directly to Django.

Instead,

the request first reaches a reverse proxy like Nginx.

Nginx is responsible for things such as

- SSL Termination
- Serving Static Files
- Load Balancing
- Request Routing
- Compression

One common mistake people make is assuming Django serves everything.

In production,

Django rarely serves static assets.

Images,

CSS,

JavaScript,

and other static files are usually handled directly by Nginx or a CDN because they're much more efficient at it.

---

# Gunicorn / Uvicorn

Django itself isn't an HTTP server.

It needs an application server to run.

For synchronous Django applications,

that's usually Gunicorn.

For asynchronous Django,

it's commonly Uvicorn.

Think of these as the processes responsible for running your Django application and accepting requests forwarded by Nginx.

One thing interviewers sometimes ask is

> Why can't I just run `python manage.py runserver` in production?

Because `runserver` is a development server.

It's designed for developer convenience,

not production workloads.

Production servers provide

- Worker Processes
- Better Concurrency
- Timeouts
- Graceful Restarts
- Process Management

which are essential in real deployments.

---

# WSGI vs ASGI

Once Gunicorn or Uvicorn receives the request,

it communicates with Django through either

```
WSGI

or

ASGI
```

WSGI is designed for synchronous applications.

One request occupies one worker until it finishes.

ASGI extends Django to support asynchronous communication,

making it suitable for

- WebSockets
- Server-Sent Events
- Long-lived Connections
- Async Views

Most traditional Django applications still work perfectly with WSGI.

Async should solve a problem,

not be adopted simply because it's newer.

---

# Middleware

Before the request reaches your view,

it passes through Django's middleware stack.

I think of middleware as request interceptors.

Every request passes through them,

and every response passes back through them.

Common production examples include

- Authentication
- Logging
- Correlation IDs
- Rate Limiting
- Tenant Resolution
- Security Headers
- Request Timing

One thing I like about middleware is that it lets you solve cross-cutting concerns once instead of repeating the same code across every view.

If I wanted to log every incoming request,

middleware is probably where I'd start rather than adding logging inside every API endpoint.

---

# URL Resolver

After middleware,

Django determines which view should handle the request.

```
GET /users/42

↓

users.urls

↓

UserDetailView
```

The URL Dispatcher maps incoming URLs to the appropriate view function or class.

This separation keeps routing logic independent from business logic,

making applications easier to organize as they grow.

---

# Django Interview Handbook

...

# Django Request Lifecycle

## Interviewer

Walk me through what happens when a request reaches your Django application.

---

## Answer

Sure.

Let's say I open

GET /users/42

The first thing to understand is that the request doesn't immediately reach Django.

There are several components involved before my code even starts executing.

```
Client

↓

Nginx

↓

Gunicorn / Uvicorn

↓

WSGI / ASGI

↓

Django Middleware

↓

URL Resolver

↓

View

↓

Business Logic

↓

ORM

↓

Database

↓

Response
```

Whenever I debug production issues, this flow is usually where I start because latency can be introduced at almost every stage.

For example,

sometimes people immediately blame the database when an endpoint becomes slow.

But in reality the bottleneck could be

- middleware
- serialization
- authentication
- network calls
- external APIs

So understanding this request lifecycle makes debugging much easier.

Let's go through every component.

---

## Interviewer

Why is Nginx sitting in front of Django?

---

## Answer

Django isn't designed to be exposed directly to the internet.

Something has to accept incoming HTTP requests first.

That's usually Nginx.

Think of Nginx as the front door to your application.

Whenever a request comes in,

Nginx decides what should happen next.

For example,

if someone requests

```
/static/logo.png
```

there's no reason for Django to even know about it.

Nginx can serve that file directly.

If the request is

```
GET /users/42
```

then Nginx forwards it to Django.

Besides request routing,

Nginx usually handles things like

- SSL Termination
- Static Files
- Compression
- Load Balancing
- Reverse Proxying

One mistake I see juniors make is assuming Django serves everything.

In production,

Django rarely serves static assets.

That work is almost always delegated to Nginx or a CDN.

---

## Interviewer

Then why do we need Gunicorn?

Can't Nginx directly run Django?

---

## Answer

No.

Nginx understands HTTP.

Django understands Python.

Something has to execute the Python application.

That's Gunicorn.

Think of it like this.

```
Browser

↓

Nginx

↓

Gunicorn

↓

Django
```

Gunicorn starts multiple worker processes,

loads your Django application into memory,

and hands incoming requests to those workers.

Without Gunicorn,

Nginx has no idea how to execute Python code.

---

## Interviewer

Then what's the difference between Gunicorn and runserver?

---

## Answer

`runserver` is only meant for development.

Its job is to make local development easy.

It automatically reloads code whenever I save a file,

shows detailed error pages,

and gives me a simple HTTP server.

Production has completely different requirements.

I need

- multiple workers
- graceful restarts
- timeouts
- process management
- better concurrency

That's why we use Gunicorn instead.

I've never seen anyone deploy `runserver` to production.

---

## Interviewer

What about Uvicorn?

When would you use that instead?

---

## Answer

Gunicorn works great for synchronous Django applications.

If my application starts using async views,

WebSockets,

or long-lived connections,

then I'd move towards ASGI and typically use Uvicorn.

That doesn't automatically make it faster though.

One mistake people make is thinking async means faster.

It really depends on the workload.

If my API spends most of its time waiting on external services,

async can improve throughput.

If it's CPU-intensive,

async won't magically solve the problem.

So I usually choose async because I have an async problem,

not because async is newer.

---

## Interviewer

What exactly is WSGI and ASGI?

---

## Answer

I think of WSGI and ASGI as contracts.

Gunicorn doesn't know anything about Django.

Django doesn't know anything about Gunicorn.

They need a standard way to communicate.

That's what WSGI provides.

```
Gunicorn

↓

WSGI

↓

Django
```

ASGI is basically the evolution of WSGI.

It supports

- async requests
- WebSockets
- background communication
- long-lived connections

Traditional Django applications work perfectly with WSGI.

If I'm building chat applications,

notifications,

or anything requiring asynchronous communication,

then ASGI becomes the better choice.

---

## Interviewer

What happens after Django receives the request?

---

## Answer

The first thing Django does is send the request through its middleware stack.

I usually think of middleware as request interceptors.

Every request passes through them before reaching my view,

and every response passes back through them before going back to the client.

It's a great place to solve problems that every request shares.

For example,

I've used middleware for

- Authentication
- Request Logging
- Correlation IDs
- Tenant Resolution
- Request Timing
- Security Headers

instead of repeating the same code in every API.

If tomorrow I wanted to log every request,

I'd write one middleware,

not modify fifty different views.

That's one of the reasons middleware is so powerful.

---

## Interviewer

What happens after middleware?

---

## Answer

Once middleware finishes,

Django needs to figure out which view should handle the request.

That's where the URL Resolver comes in.

Suppose someone requests

```
GET /users/42
```

Django looks through the URL patterns,

finds the matching route,

and dispatches the request to the corresponding view.

```
GET /users/42

↓

urls.py

↓

UserDetailView
```

From there,

the actual business logic starts executing.

That's where most interview discussions naturally move into Django Views, ORM, QuerySets, and database interactions.