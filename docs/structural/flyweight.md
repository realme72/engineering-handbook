# Flyweight Pattern

## Intent

The Flyweight Pattern optimizes memory usage by avoiding the creation of duplicate objects that share the same immutable state.

Instead of every object maintaining its own copy of identical data, the pattern stores the shared state only once and allows multiple objects to reference it. Each object then maintains only the information that is unique to it.

The primary goal of the Flyweight Pattern is to reduce memory consumption without changing the behavior of individual objects.

### What does the pattern do?

It reduces memory consumption by sharing immutable state across multiple objects instead of duplicating it.

### How does it work?

The pattern separates an object's state into two categories:

- **Intrinsic State**: Shared, immutable data that can be reused across multiple objects.
- **Extrinsic State**: Object-specific data supplied by the client during runtime.

Each object references the shared Flyweight object instead of storing duplicate copies of the same information.

### What structural problem does it solve?

It prevents unnecessary memory consumption when an application needs to create a large number of similar objects that share most of their state.

---

## Why Was This Pattern Introduced?

Consider a map application such as Google Maps.

Suppose the application displays thousands of restaurant locations.

Every restaurant marker contains:

- Restaurant Icon
- Marker Color
- Marker Shape
- Rendering Logic

A naive implementation stores all of this data inside every marker.

```text
Restaurant Marker

├── Icon
├── Color
├── Shape
├── Latitude
└── Longitude
```

If there are one million restaurants,

the application also creates

- One million identical icons
- One million identical colors
- One million identical rendering configurations

This wastes a significant amount of memory because these values never change.

The only information that differs is the restaurant's location.

The Flyweight Pattern solves this by storing the shared marker information once and allowing every restaurant marker to reference it.

```text
Restaurant Marker

↓

Restaurant Marker Type

├── Icon
├── Color
└── Shape

+

Latitude

Longitude
```

The application now stores one shared marker configuration while every marker supplies only its own coordinates.

---

## Real-World Analogy

Imagine a classroom where every student receives the same textbook.

A naive approach would print a new textbook for every student.

Instead, the school maintains one master copy of the book and distributes identical copies.

The content of the textbook never changes.

The only thing unique to each student is:

- Student Name
- Roll Number
- Seat Number

Similarly, Flyweight separates shared information from object-specific information.

---

## Software Engineering Example

A map application displaying restaurant locations is an excellent production example.

Instead of every marker storing

```text
Restaurant Marker

├── Icon
├── Color
├── Shape
├── Latitude
└── Longitude
```

we separate the shared information.

Shared (Intrinsic State)

```text
RestaurantMarkerType

├── Icon
├── Color
└── Shape
```

Unique (Extrinsic State)

```text
Restaurant Marker

├── Latitude
└── Longitude
```

Every restaurant marker references the same `RestaurantMarkerType` object.

This dramatically reduces memory usage when rendering thousands or millions of markers.

Other production examples include:

- Google Maps markers
- Country metadata shared across users
- Chess pieces
- Text editor character glyphs
- Game engine assets (textures, meshes, models)
- ORM metadata caches

---

## Python Implementation

```python
class MarkerType:

    def __init__(self, icon, color):
        self.icon = icon
        self.color = color

    def render(self, latitude, longitude):
        print(
            f"Rendering {self.icon} ({self.color}) "
            f"at ({latitude}, {longitude})"
        )


class MarkerFactory:

    _marker_types = {}

    @classmethod
    def get_marker(cls, icon, color):

        key = (icon, color)

        if key not in cls._marker_types:
            cls._marker_types[key] = MarkerType(icon, color)

        return cls._marker_types[key]


class Restaurant:

    def __init__(self, latitude, longitude, marker_type):
        self.latitude = latitude
        self.longitude = longitude
        self.marker_type = marker_type

    def display(self):
        self.marker_type.render(self.latitude, self.longitude)


restaurant_marker = MarkerFactory.get_marker(
    "Restaurant",
    "Red"
)

r1 = Restaurant(12.9716, 77.5946, restaurant_marker)
r2 = Restaurant(12.9822, 77.6100, restaurant_marker)
r3 = Restaurant(12.9755, 77.6202, restaurant_marker)

r1.display()
r2.display()
r3.display()
```

**Output**

```text
Rendering Restaurant (Red) at (12.9716, 77.5946)

Rendering Restaurant (Red) at (12.9822, 77.6100)

Rendering Restaurant (Red) at (12.9755, 77.6202)
```

Notice that all three restaurants share the same `MarkerType` object.

---

## Internal Workflow

When the client creates a restaurant marker,

```python
restaurant = Restaurant(
    latitude,
    longitude,
    marker_type
)
```

the following sequence occurs.

```text
Client

        │

        ▼

MarkerFactory

        │

Marker Exists?

│

├── Yes

│     │

│     ▼

│ Return Existing MarkerType

│

└── No

      │

      ▼

Create MarkerType

      │

      ▼

Store for Reuse

      │

      ▼

Restaurant Object
```

Each restaurant stores only:

- Latitude
- Longitude

The shared marker configuration exists only once.

---

## How to Identify This Pattern

You are likely looking at a Flyweight Pattern if you notice:

- Thousands or millions of similar objects.
- Large amounts of duplicated immutable state.
- A factory responsible for sharing existing objects.
- Objects storing references to shared immutable data instead of duplicating it.

---

## Advantages

- ✅ Significantly reduces memory consumption.
- ✅ Eliminates duplicated immutable state.
- ✅ Improves scalability for large object graphs.
- ✅ Centralizes shared object management.
- ✅ Encourages reuse of immutable objects.

---

## Disadvantages

- ❌ Introduces additional design complexity.
- ❌ Requires careful separation of intrinsic and extrinsic state.
- ❌ Shared objects should generally be immutable.
- ❌ Little benefit when the number of objects is small.

---

## When Should You Use It?

Use the Flyweight Pattern when:

- The application creates a very large number of similar objects.
- Most object state is identical.
- Memory consumption becomes a concern.
- Shared state can be made immutable.

---

## When Should You Avoid It?

Avoid the Flyweight Pattern when:

- Objects are highly unique.
- Memory usage is not a concern.
- Separating intrinsic and extrinsic state complicates the design unnecessarily.

---

## Common Interview Questions

### Basic

- What problem does the Flyweight Pattern solve?
- What is intrinsic state?
- What is extrinsic state?

### Intermediate

- Why does Flyweight improve memory efficiency?
- Why should intrinsic state be immutable?
- Explain the role of the Flyweight Factory.

### Advanced

- Design a map application using the Flyweight Pattern.
- Explain how Flyweight is used in game engines.
- Where have you encountered Flyweight in backend systems?
- How would you implement a thread-safe Flyweight Factory?

---

## Related Patterns

| Pattern | Difference |
|----------|------------|
| Composite | Composite models hierarchical tree structures. Flyweight optimizes memory by sharing object state. |
| Proxy | Proxy controls access to an object. Flyweight shares immutable state between objects. |
| Bridge | Bridge separates abstraction from implementation. Flyweight separates shared state from unique state. |
| Singleton | Singleton ensures only one instance exists. Flyweight manages many shared instances based on intrinsic state. |

---

## Key Takeaways

- The Flyweight Pattern reduces memory usage by sharing immutable state between multiple objects.
- It separates an object's state into intrinsic (shared) and extrinsic (unique) state.
- A Flyweight Factory ensures that shared objects are reused instead of recreated.
- Google Maps markers, game engine assets, character glyphs, and country metadata are excellent production examples.
- Flyweight is valuable only when creating a large number of similar objects where duplicated state would otherwise consume significant memory.

---

## Interview Answer

### How would you explain the Flyweight Pattern in an interview?

> The Flyweight Pattern is a structural design pattern that optimizes memory usage by sharing immutable state across multiple objects instead of storing duplicate copies in every object.
>
> It achieves this by separating an object's state into **intrinsic state**, which is common and shared, and **extrinsic state**, which is unique to each object and supplied at runtime. A Flyweight Factory is typically responsible for creating and reusing shared instances based on their intrinsic state.
>
> The pattern is particularly useful when an application creates a very large number of similar objects where most of their state is identical. By sharing the common state instead of duplicating it, Flyweight significantly reduces memory consumption while preserving the object's behavior.
>
> A good production example is a map application. Thousands of restaurant markers may share the same icon, color, shape, and rendering logic. Instead of every marker storing this identical information, a single shared `MarkerType` object is reused by all markers, while each marker stores only its unique latitude and longitude.
>
> I generally consider Flyweight when memory usage becomes a bottleneck and I notice that many objects differ only by a small amount of state. If objects are highly unique or memory isn't a concern, introducing Flyweight usually adds unnecessary complexity.
