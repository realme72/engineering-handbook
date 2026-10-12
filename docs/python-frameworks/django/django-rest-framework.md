# Django REST Framework Interview Questions & Answers

> This handbook is written as if you're sitting in a Senior Backend Engineer interview.
>
> Every answer focuses on **how experienced engineers think**, not on memorizing the documentation.
>
> Instead of definitions, every answer starts with the problem that DRF is trying to solve.

---

# Table of Contents

1. Why Django REST Framework?
2. APIView vs Django View
3. GenericAPIView
4. ViewSet vs APIView
5. ViewSet vs ModelViewSet
6. Serializers
7. ModelSerializer
8. Validation
9. Authentication
10. Permissions
11. Pagination
12. Filtering & Searching
13. Exception Handling
14. Throttling
15. Versioning
16. Performance
17. Production Questions

---

# Question 1

## Interviewer

**Why does Django REST Framework exist? Django already has Views.**

---

## Answer

That's actually the first question I asked myself when I started using DRF.

If Django already lets me write views, why introduce another framework?

Let's imagine DRF didn't exist.

Suppose I'm building

```
GET /users
```

The first thing I'd write is

```python
def get_users(request):
```

Querying the database is easy.

```python
users = User.objects.all()
```

But now I need to

- convert model objects into JSON
- validate incoming requests
- parse request bodies
- authenticate users
- authorize requests
- paginate results
- handle exceptions
- return proper HTTP status codes

None of these are difficult individually.

The problem is that every API needs all of them.

After building a few APIs,

every project starts creating

- Base Views
- JSON Helpers
- Validation Helpers
- Pagination Helpers
- Authentication Helpers

Everyone is solving exactly the same problems.

That's where DRF comes in.

Instead of every team writing API infrastructure,

DRF standardizes it.

Now I can inherit from

```python
APIView
```

or

```python
ModelViewSet
```

and focus almost entirely on business logic.

That's how I think about DRF.

It's not just a framework for REST APIs.

It's a framework that solves all the repetitive plumbing every REST API eventually needs.

---

# Question 2

## Interviewer

**APIView vs Django View. Why use APIView?**

---

## Answer

Suppose I build an API using a normal Django View.

```python
def users(request):
```

Everything is manual.

I need to

- parse JSON
- validate input
- authenticate
- return JsonResponse
- handle unsupported methods
- catch exceptions

Now imagine I have 200 APIs.

I'm writing the same code again and again.

APIView already knows it's dealing with APIs.

Instead of writing

```python
if request.method == "GET":
```

I simply write

```python
class UserAPIView(APIView):

    def get(self, request):
        ...

    def post(self, request):
        ...
```

APIView automatically provides

- Request parsing
- Authentication
- Permissions
- Throttling
- Content negotiation
- Exception handling

I think of APIView as Django View specialized for REST APIs.

---

# Question 3

## Interviewer

**Then why GenericAPIView? Isn't APIView enough?**

---

## Answer

APIView removes a lot of HTTP boilerplate.

But after writing a few APIs,

I noticed another pattern.

Almost every endpoint looks like

```
Query Database

↓

Serialize

↓

Return Response
```

Again.

Again.

Again.

For example

```
List Users

↓

List Products

↓

List Orders

↓

List Payments
```

The flow barely changes.

Only the model changes.

GenericAPIView recognizes that pattern.

Instead of repeatedly writing

```python
users = User.objects.all()
serializer = UserSerializer(users, many=True)
```

I simply define

```python
queryset

serializer_class
```

and GenericAPIView handles the common behavior.

It doesn't remove flexibility.

It removes repetition.

---

# Question 4

## Interviewer

**APIView vs GenericAPIView. Which one do you use?**

---

## Answer

It depends on how much customization I need.

If I'm building something completely custom,

I'll start with APIView.

For example,

payment callbacks,

OAuth flows,

or anything that doesn't naturally fit CRUD.

If the endpoint is essentially CRUD,

I almost always start with GenericAPIView or one of DRF's generic views.

There's no point writing boilerplate if DRF already solved it.

I generally choose the highest abstraction that still lets me express the business logic clearly.

---

# Question 5

## Interviewer

**Then why ViewSets?**

---

## Answer

Imagine I have a User API.

Without ViewSets I'd probably write

```
UserListAPIView

UserDetailAPIView

UserUpdateAPIView

UserDeleteAPIView
```

Each one handles part of the same resource.

As the project grows,

the number of views grows quickly.

ViewSets group all operations on the same resource together.

Instead of multiple classes,

I simply write

```python
class UserViewSet(...)
```

Inside that class,

DRF understands

- list()
- retrieve()
- create()
- update()
- destroy()

Everything related to Users lives together.

I find this much easier to navigate in larger projects.

---

# Question 6

## Interviewer

**APIView vs ViewSet. Which one do you prefer?**

---

## Answer

I don't think one is better than the other.

They're solving different problems.

If the endpoint naturally represents a resource,

ViewSets are fantastic.

Users.

Orders.

Products.

Invoices.

Everything fits nicely.

But not every endpoint is CRUD.

For example,

```
POST /payments/webhook

POST /oauth/callback

POST /login

POST /logout
```

These are operations,

not resources.

Trying to force them into a ViewSet usually makes the code worse.

So I generally ask myself

> "Is this endpoint resource-oriented?"

If yes,

ViewSet.

If no,

APIView.

---

# Question 7

## Interviewer

**What is a Serializer?**

---

## Answer

Suppose I fetch users from the database.

```python
users = User.objects.all()
```

Django gives me Python objects.

The browser doesn't understand Python objects.

It understands JSON.

So somewhere I need to convert

```
Python Objects

↓

JSON
```

Without serializers,

I'd manually write

```python
{
    "id": user.id,
    "name": user.name
}
```

for every model.

Eventually,

I'd have hundreds of these mappings across the project.

Serializers solve that problem.

They know how to

- convert model objects into JSON
- validate incoming JSON
- convert JSON back into Python objects

So I usually think of a Serializer as the translator between Django models and HTTP.

---

# Question 8

## Interviewer

**Serializer vs ModelSerializer**

---

## Answer

ModelSerializer is really just a shortcut.

If my serializer maps almost one-to-one with my model,

I'll use ModelSerializer.

It automatically generates fields and validators.

But there are many situations where my API doesn't match my database schema.

Maybe I need

- computed fields
- nested objects
- merged responses
- external API data

At that point,

I switch to Serializer because I want complete control.

So my decision is based on how closely the API matches the underlying model.

---

# Question 9

## Interviewer

**Where does validation happen in DRF?**

---

## Answer

One thing I like about DRF is that validation happens before my business logic executes.

The request flow is roughly

```
Request

↓

Serializer

↓

Validation

↓

View

↓

Business Logic
```

If validation fails,

my view never runs.

That keeps business logic much cleaner.

Instead of checking

```
Is email valid?

Is age valid?

Is password empty?
```

inside every API,

I let the serializer handle it.

The view assumes it's working with already validated data.

That's a much cleaner separation of responsibilities.

---

# Question 10

## Interviewer

**Authentication vs Permissions**

---

## Answer

I think of them as answering two completely different questions.

Authentication asks

> Who are you?

Permissions ask

> Now that I know who you are,
> are you allowed to do this?

The flow usually looks like

```
Request

↓

Authentication

↓

request.user

↓

Permissions

↓

View
```

Authentication establishes identity.

Permissions decide access.

Keeping those responsibilities separate makes the authorization layer much easier to reason about.

---

# Coming Next

The remaining interview questions cover

- Pagination
- Filtering
- Search
- Ordering
- Versioning
- Exception Handling
- Throttling
- Performance
- Production Scenarios

These topics naturally build on the concepts covered above and are best understood after APIViews, ViewSets, and Serializers.