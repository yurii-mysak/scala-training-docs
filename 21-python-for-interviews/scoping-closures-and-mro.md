# Scoping, Closures & MRO

> **Priority:** Recommended
> **Est. time:** 40 min
> **Track:** Both
> **HelloInterview:** Low-Level Design in a Hurry

[oop-and-design-in-python.md](oop-and-design-in-python.md) covers classes, dunder methods, composition,
and a full worked stateful-class design — the vocabulary for "implement a class" prompts. This file is
the layer underneath: how Python actually resolves a name, how a closure captures one, how a decorator
is just a closure with a specific shape, and how multiple inheritance actually dispatches a method call
once more than one base class is involved. None of this duplicates that file — §8 here builds directly
on its §1 (`super().__init__()` isn't automatic) and §5 (composition over inheritance).

---

## 1 · The LEGB rule

Every name lookup in Python checks, in order: **L**ocal (the current function), **E**nclosing (any
function this one is nested inside), **G**lobal (the module), **B**uilt-in (`len`, `range`, `Exception`,
...). The first scope that defines the name wins; nothing past it is even consulted.

```python
x = "global x"

def outer():
    x = "enclosing x"
    def inner():
        x = "local x"
        print("local:", x)          # finds it in L -- stops there
    inner()
    print("enclosing:", x)           # inner's L didn't apply here; this is outer's own L

outer()
print("global:", x)

def show_builtin():
    print("builtin, e.g. len:", len)   # not local, not enclosing, not global -> falls through to B

show_builtin()
```

There is a sharp compile-time consequence worth having seen once: **assigning to a name anywhere inside
a function makes Python treat every reference to that name, anywhere in that function, as local** — even
on lines that run *before* the assignment. It's decided when the function is compiled, not evaluated
line by line at runtime:

```python
counter = 0

def increment_broken():
    counter += 1        # UnboundLocalError -- the assignment below makes `counter` local
                         # for the WHOLE function, so this read sees the local (unassigned yet),
                         # not the global

increment_broken()   # UnboundLocalError
```

This exact trap, from the transfer-errors angle, is already worked through in
[from-lua-and-scala-to-python.md, mistake #15](from-lua-and-scala-to-python.md#4--the-top-20-mistakes-on-day-one) —
worth a second look now that you have the general rule (LEGB plus "assignment always declares local")
behind it, not just the symptom.

---

## 2 · `global` and `nonlocal`

Both exist for exactly one purpose: **telling Python that an assignment inside this function should
target an outer scope's variable, not create a new local one.** Reading an outer variable never needs
either keyword — only assigning to it does.

```python
counter = 0

def increment_fixed():
    global counter          # without this, the same UnboundLocalError from §1 happens
    counter += 1

increment_fixed()
print(counter)   # 1
```

`nonlocal` is `global`'s counterpart for an *enclosing function's* variable — neither local nor
module-global, the middle "E" of LEGB:

```python
def make_counter():
    count = 0
    def increment():
        nonlocal count      # targets make_counter's `count`, not a new local, not the module global
        count += 1
        return count
    return increment

counter = make_counter()
print(counter(), counter(), counter())   # 1 2 3
```

`nonlocal` must find a matching variable in *some* enclosing function scope — not the module level, that
is what `global` is for — or it's a `SyntaxError` at compile time, before the function ever runs:

```python
src = """
def outer():
    def inner():
        nonlocal missing   # no enclosing binding named `missing` exists anywhere
    inner()
"""
compile(src, "<demo>", "exec")   # SyntaxError: no binding for nonlocal 'missing' found
```

---

## 3 · Closures — capturing the variable, not the value

A closure is a function that references a name from an enclosing scope. What actually gets captured is
**the variable itself — a reference to it, via a `cell` object — not a snapshot of its value at the
moment the closure was created.** If the enclosing variable changes later, the closure sees the new
value, because it was never holding a copy:

```python
def demo():
    message = "original"
    def printer():
        print("closure sees:", message)
    printer()
    message = "changed after the closure was created"
    printer()          # sees the NEW value -- it captured the variable, not a point-in-time copy

demo()
# closure sees: original
# closure sees: changed after the closure was created
```

`__closure__` makes this literal and inspectable — it's a tuple of `cell` objects, one per captured
variable, each holding a live reference:

```python
def make_printer():
    message = "created inside the factory"
    def printer():
        print(message)
    return printer

p = make_printer()
print(p.__closure__[0].cell_contents)   # created inside the factory
```

### 3.1 The late-binding-in-a-loop gotcha, and its two fixes

The single most common closure bug, and it's already been met once from the Lua-transfer angle in
[from-lua-and-scala-to-python.md, §2.1](from-lua-and-scala-to-python.md) — worth seeing
again here in its general form, since it's really just §1's LEGB rule plus §3's "captures the variable,
not the value" landing on the same loop variable at once. A closure created inside a loop captures the
loop variable itself, and the loop variable is **one variable, reassigned each iteration** — not a fresh
binding per iteration the way some other languages give you. By the time any of the closures actually
run, the loop has finished, and they all see whatever the variable's final value was:

```python
funcs = [lambda: i for i in range(3)]
print([f() for f in funcs])    # [2, 2, 2] -- NOT [0, 1, 2]
```

**Fix 1 — bind it as a default argument**, evaluated at *definition* time rather than call time (already
shown in the Lua-transfer file, repeated here for completeness):

```python
funcs = [lambda i=i: i for i in range(3)]
print([f() for f in funcs])    # [0, 1, 2]
```

**Fix 2 — wrap it in a factory function.** A real function call creates a genuinely new local scope on
every invocation, so passing the loop variable in as an argument pins that iteration's value the same
way, without relying on a default-argument trick — and it reads better once the closure body is more
than one expression, where the `lambda i=i:` idiom gets awkward fast:

```python
def make_func(i):
    return lambda: i

funcs = [make_func(i) for i in range(3)]
print([f() for f in funcs])    # [0, 1, 2]
```

The same fact is *why* `asyncio.create_task(worker(i))` inside a loop is safe — `i` is passed as a real
argument across a function-call boundary into `worker`, not captured by a closure over the loop
variable — see [async-and-concurrency.md](async-and-concurrency.md).

---

## 4 · Writing decorators from scratch

A decorator is just a function that takes a callable and returns a callable — `@decorator` above a
function definition is exactly `func = decorator(func)`, no more magic than that.

**Plain decorator:**

```python
import time

def timed(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.6f}s")
        return result
    return wrapper

@timed
def add(a, b):
    return a + b

print(add(2, 3))
```

**Decorator with arguments** needs one more level of nesting: the outermost function takes the
decorator's own arguments and returns the actual decorator, which takes the function and returns the
wrapper:

```python
import functools

def retry(times):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except ValueError as exc:
                    last_exc = exc
                    print(f"attempt {attempt + 1} failed: {exc}")
            raise last_exc
        return wrapper
    return decorator

calls = {"n": 0}

@retry(times=3)
def flaky():
    calls["n"] += 1
    if calls["n"] < 3:
        raise ValueError(f"not ready (call {calls['n']})")
    return "ok"

print(flaky())
```

**Class-based decorator** — implement `__init__(self, func)` to receive the decorated function, and
`__call__` to make instances themselves callable:

```python
class CountCalls:
    def __init__(self, func):
        self._func = func
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1
        return self._func(*args, **kwargs)

@CountCalls
def greet(name):
    return f"hi {name}"

print(greet("a"), greet("b"))
print("call count:", greet.count)   # a class-based decorator can hold state a plain closure can't as cleanly
```

Reach for the class form specifically when the decorator needs to expose state or extra methods to the
caller (`greet.count` above) — a plain closure can hold state too (§3), but has no clean way to expose
it as an attribute the way an object naturally does.

### 4.1 `functools.wraps`, and why skipping it breaks introspection

The wrapper functions above all replace the original function's identity — `func.__name__`, `__doc__`,
and signature all become the wrapper's, not the original's, unless something fixes that:

```python
import functools, inspect

def noop_bad(f):
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper

def noop_good(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper

@noop_bad
def hello():
    """Says hello."""
    return "hello"

@noop_good
def hi():
    """Says hi."""
    return "hi"

print(hello.__name__, "-", hello.__doc__)   # wrapper - None  -- identity lost
print(hi.__name__, "-", hi.__doc__)          # hi - Says hi.   -- preserved
print(inspect.signature(hi))                  # ()  -- inspect still works through the wrapper
```

This isn't cosmetic. `help(hello)` shows the wrapper's blank docstring instead of the real one;
`hello.__name__` shows up as `"wrapper"` in any logging or error message that uses it; a debugger
stepping into `hello()` announces itself as `wrapper`. `functools.wraps` fixes all of it in one line and
additionally sets `__wrapped__`, letting tools like `inspect.signature` see through the decorator to the
original function's real signature. There is no cost to adding it — always decorate the wrapper with
`@functools.wraps(func)` unless you have a specific reason not to.

---

## 5 · Single inheritance and `super()` — the mechanism, briefly

[oop-and-design-in-python.md §1](oop-and-design-in-python.md) already covered the practical trap
(`super().__init__()` isn't automatic). Mechanically, `super()` doesn't mean "the parent class" — it
returns a proxy that resolves methods by walking the **MRO** (§7) starting *after* the class the `super()`
call is written in. For single inheritance that's indistinguishable from "call the parent," which is why
the distinction only becomes visible — and important — the moment there's more than one base class.

---

## 6 · Multiple inheritance and mixins

A **mixin** is a class designed to be combined with others to add one specific piece of behavior — it's
not meant to be instantiated alone, and typically has no `__init__` of its own beyond what it inherits
cooperatively:

```python
class LoggingMixin:
    def log(self, msg):
        print(f"[{type(self).__name__}] {msg}")

class SerializableMixin:
    def to_dict(self):
        return {k: v for k, v in vars(self).items() if not k.startswith("_")}

class User(LoggingMixin, SerializableMixin):
    def __init__(self, name, age):
        self.name = name
        self.age = age

u = User("amy", 30)
u.log("created")            # [User] created
print(u.to_dict())          # {'name': 'amy', 'age': 30}
```

This is idiomatic multiple inheritance — each mixin is single-purpose and independent, so composing them
doesn't create the layered "which parent's method actually runs" ambiguity real multi-parent hierarchies
can. That ambiguity is exactly what §7's C3 linearization exists to resolve deterministically when it
does come up.

---

## 7 · The MRO and C3 linearization

The **Method Resolution Order** is the specific, deterministic sequence of classes Python searches, in
order, to find a method — stored as `Cls.__mro__` (a tuple) or `Cls.mro()` (a list). For single
inheritance it's just "this class, then its parent, then its parent's parent," but multiple inheritance
needs a real algorithm to produce one consistent order, and Python uses **C3 linearization**. Two
informal rules capture what it guarantees:

- A subclass always comes before its own base classes in the order.
- The left-to-right order of base classes in a class's own definition (`class D(B, C):`) is preserved.

```python
class A:
    def greet(self):
        print("A")

class B(A):
    def greet(self):
        print("B")
        super().greet()

class C(A):
    def greet(self):
        print("C")
        super().greet()

class D(B, C):
    def greet(self):
        print("D")
        super().greet()

print([cls.__name__ for cls in D.__mro__])   # ['D', 'B', 'C', 'A', 'object']
D().greet()
```

Not every combination of base classes is even legal — if two classes' own declared orderings genuinely
conflict, C3 has no consistent linearization to produce, and Python raises `TypeError: Cannot create a
consistent method resolution order` at class-definition time rather than silently picking one.

---

## 8 · Why `super()` is cooperative, not "call the parent"

The diamond above is the concrete proof: `D`'s MRO is `D → B → C → A → object`. Calling `D().greet()`
prints `D`, then `B`'s `super().greet()` — and `B`'s own textual parent is `A`, but `super()` does
**not** call `A` directly. It calls **whatever comes next in the MRO of the actual runtime type of
`self`**, which is `C`, not `B`'s own base class:

```
D
B
C
A
```

This is the entire meaning of "cooperative multiple inheritance": every `super().greet()` call resolves
relative to the MRO of the *whole object's* class (`D`, here), not relative to the class the `super()`
call happens to be written in. `B` has no idea `D` or `C` exist, and doesn't need to — it just calls
`super()` and trusts the MRO to route the call correctly for whatever concrete class it ends up being
part of. That's what makes the pattern compose: every class in the chain has to call `super()` (not
skip it, not call a named parent directly) for the full chain to run, which is why a class that forgets
`super().__init__(...)` — the trap named in
[oop-and-design-in-python.md §1](oop-and-design-in-python.md) — breaks cooperative multiple inheritance
specifically, not just single inheritance.

---

## 9 · `__slots__` vs `__dict__` — brief

By default, every instance carries its own `__dict__` to hold attributes, which is flexible (add any
attribute at any time) but costs real memory per instance. `__slots__` trades that flexibility for a
fixed, pre-declared set of attributes stored more compactly, with no per-instance `__dict__` at all:

```python
class WithSlots:
    __slots__ = ("x",)
    def __init__(self, x):
        self.x = x

ws = WithSlots(1)
print(hasattr(ws, "__dict__"))   # False
ws.y = 2                          # AttributeError: 'WithSlots' object has no attribute 'y'
```

This is exactly what `_Node` in the manual LRU-cache fallback in
[oop-and-design-in-python.md §9](oop-and-design-in-python.md) already used, without explanation — worth
recognizing now: many small, short-lived, fixed-shape objects (linked-list nodes, points, anything you
allocate a lot of) is precisely when `__slots__`'s memory savings matter enough to reach for it.

Two things worth knowing before using it: it matters only at the scale of many instances — for a handful
of objects it's not worth the lost flexibility — and **a subclass that doesn't declare its own
`__slots__` gets a `__dict__` back anyway**, silently erasing the parent's savings:

```python
class SlottedBase:
    __slots__ = ("x",)

class NotReallySlotted(SlottedBase):
    pass                     # forgot to declare __slots__ here

n = NotReallySlotted()
n.x = 1
n.y = 2                        # works! -- the memory benefit is gone the moment this subclass exists
print(hasattr(n, "__dict__"))  # True
```

---

## 10 · `__getattr__` / `__setattr__` — brief

`__getattr__(self, name)` is a **fallback**: it only runs when normal attribute lookup already failed —
not an instance attribute, not found on the class. It's the idiomatic way to make an object look like it
has dynamic attributes backed by something else (a dict, a config source):

```python
class Config:
    def __init__(self, **kwargs):
        self._data = kwargs
    def __getattr__(self, name):
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(name)   # keep the contract: missing means AttributeError, not KeyError

c = Config(host="localhost", port=8080)
print(c.host, c.port)   # localhost 8080
```

`__setattr__(self, name, value)`, in contrast, intercepts **every** attribute assignment, with no
"only on failure" escape hatch — including assignments inside `__init__` itself. Writing `self.name =
value` naively inside `__setattr__` calls `__setattr__` again, recursing until `RecursionError`:

```python
class TrulyBroken:
    def __setattr__(self, name, value):
        self.name = value    # recurses: this assignment invokes __setattr__ again

try:
    TrulyBroken().x = 1
except RecursionError:
    print("RecursionError, as expected")

class Fixed:
    def __setattr__(self, name, value):
        self.__dict__[name] = value   # bypass __setattr__ entirely -- write the dict directly

f = Fixed()
f.x = 5
print(f.x)   # 5
```

The fix is always some form of "bypass the override" — write directly to `self.__dict__[name]`, or call
`super().__setattr__(name, value)` if a base class's behavior should still run.

---

## Interview questions

1. **What are the four scopes LEGB checks, in order, and which one does a bare `def inner():` nested
   inside another function add?** Local, Enclosing, Global, Built-in, checked in that order until the
   name is found. A nested function adds an *Enclosing* scope — the outer function's locals become
   visible to the inner one, but only for reading unless `nonlocal` is used to write to them.

2. **A closure over a loop variable returns the same final value from every copy. Why, and what are the
   two ways to fix it?** The loop variable is one variable, reassigned each iteration, not a fresh
   binding per iteration — a closure captures the variable itself, so all copies see whatever it holds
   once the loop has finished. Fix 1: bind it as a default argument (`lambda i=i: ...`), evaluated at
   definition time. Fix 2: pass it into a factory function, which creates a genuinely new scope per call.

3. **Why does `functools.wraps` matter for a decorator that's otherwise working correctly?** Without it,
   the decorated function's `__name__`, `__doc__`, and signature all become the wrapper's instead of the
   original's — `help()`, logging, debuggers, and `inspect.signature` all show the wrong thing. It costs
   nothing to add and fixes all of it, including setting `__wrapped__` so tools can see through the
   wrapper to the original.

4. **What does `super()` actually resolve against — the class it's written in, or the type of the actual
   object at runtime?** The type of the actual runtime object (`type(self)`'s MRO), starting just after
   the class the `super()` call is written in. That's why it's called cooperative: in a diamond, a middle
   class's `super()` call can route to a *sibling* class, not its own textual parent, depending on what
   the full runtime MRO puts next.

5. **In a diamond `D(B, C)` where both `B` and `C` inherit from `A`, and every class calls
   `super()`, what's `D`'s MRO, and why doesn't `B`'s `super()` call go straight to `A`?** `D, B, C, A,
   object` — C3 linearization puts every subclass before its bases and preserves `D`'s own declared
   `B, C` order. `B`'s `super()` follows `D`'s MRO, not `B`'s own base list, so it lands on `C` (the next
   class in `D`'s MRO after `B`), and only `C`'s own `super()` call reaches `A`.

6. **[Reported at Lyft]** A coding-screen prompt asked candidates to "implement methods in a class." If
   that class needs to combine two independent, reusable behaviors, would you reach for multiple
   inheritance, mixins, or composition first?** Mixins are the right tool specifically when each behavior
   is genuinely independent and meant to be combined — the pattern in §6. For anything that's really "has
   a" rather than "is enhanced by," composition (already covered in
   [oop-and-design-in-python.md §5](oop-and-design-in-python.md)) is still the faster, more flexible
   default in a timed round.

7. **What's the practical trade-off in adding `__slots__` to a class, and what silently defeats it?**
   Saved per-instance memory and slightly faster attribute access, at the cost of losing dynamic
   attribute assignment and multiple-inheritance flexibility. It's silently defeated the moment a
   subclass doesn't declare its own `__slots__` — that subclass gets a full `__dict__` back, erasing the
   parent's savings for every instance of it.

8. **A class defines `__setattr__` and its own `__init__` immediately raises `RecursionError`. What's
   the bug, and what's the fix?** `__setattr__` intercepts every assignment, including the ones inside
   `__init__` itself — writing `self.name = value` directly inside `__setattr__` calls `__setattr__`
   again, recursively, forever. Fix: write to `self.__dict__[name] = value` directly, or delegate to
   `super().__setattr__(name, value)`, either of which bypasses the override instead of re-triggering it.
