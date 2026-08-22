# Web Frameworks: Flask, FastAPI, Django

> **Priority:** Optional
> **Est. time:** 50 min
> **Track:** Server + Web
> **HelloInterview:** System Design in a Hurry → Core Concepts → API Design

This file only matters if the role turns out to include the Web half of "Server or Server + Web" — see
the note on that in the program's [root README](../README.md). If it's confirmed Server-only, skip this
file entirely; nothing else in this program depends on it.

**Lyft's own Python APIs are built on Flask** — [15-system-design/lyft-architecture.md](../15-system-design/lyft-architecture.md)
names it directly, alongside Envoy, gRPC, and Protocol Buffers between services. That's why Flask leads
here, not FastAPI, even though FastAPI's async-native design and automatic validation make it the more
common choice for a *new* Python API today, and even though the target team's own LangGraph platform is
async Python throughout. Knowing Flask fluently is a concrete, checkable signal that you've engaged with
their actual stack rather than a generic "I'd reach for some framework" answer in a design round.

> Unlike the rest of this program, Flask, FastAPI, Django, Pydantic, and SQLAlchemy are all **third-party
> packages**, not standard library — this file's code is illustrative, for reading and discussion, not
> written to `python3 file.py` standalone the way every other file in this section is.

---

## 1 · Flask — the shape Lyft actually uses

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = lookup_user(user_id)
    if user is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(user)
```

**Blueprints** split routes into independent, reusable modules instead of piling every route onto one
`app` object — each blueprint is registered onto the app once, at startup:

```python
from flask import Blueprint

users_bp = Blueprint("users", __name__, url_prefix="/users")

@users_bp.route("/<int:user_id>")
def get_user(user_id):
    ...

# in the app factory:
app.register_blueprint(users_bp)
```

**The application factory pattern** — a `create_app()` function that constructs and returns the `Flask`
instance, instead of a bare module-level `app = Flask(__name__)` — is the idiomatic structure for
anything beyond a toy app:

```python
def create_app(config=None):
    app = Flask(__name__)
    app.config.update(config or {})
    app.register_blueprint(users_bp)
    return app
```

It matters for three concrete reasons: **tests** can spin up a fresh app per test with test-specific
config, instead of sharing one process-wide app object with global state; **multiple configs** (dev,
staging, prod) become a constructor argument instead of import-time branching; and it avoids **import-time
side effects** — nothing runs until `create_app()` is actually called, which matters the moment more than
one entry point needs the app (the WSGI server, a CLI script, a test harness).

**WSGI vs ASGI.** Flask is WSGI-native: one request is handled synchronously, start to finish, by one
worker (a thread or process) before that worker is free for the next request — see
[deploying-python-services.md §2](../14-cloud-and-infrastructure/deploying-python-services.md)
for exactly how gunicorn's sync/gthread/gevent workers turn that into real concurrency. Flask 2.0+ does
support `async def` view functions — but that's a compatibility shim (each async view runs its own event
loop for the duration of that one request), **not** a change to Flask's underlying concurrency model. An
`async def` view lets you `await` something inside that one handler; it does not give a worker the
ability to serve other requests while that handler awaits, the way a genuinely ASGI framework does. Don't
conflate "Flask views can be `async def`" with "Flask is now like FastAPI" — a real and common
misconception.

**Why this matters for the design rounds specifically**: an interviewer who works on this stack is
grounded in a real, synchronous, one-worker-per-request-at-a-time mental model — a blocking downstream
call in a Flask handler genuinely ties up that worker, which is exactly the `2 × cores + 1` capacity math
in [napkin-math.md §5.4](../15-system-design/napkin-math.md) and the worker-model discussion in
[deploying-python-services.md §2](../14-cloud-and-infrastructure/deploying-python-services.md).
Naming Flask, gunicorn, and that trade-off fluently in a design round reads as familiarity with their
actual production reality, not a textbook answer.

---

## 2 · FastAPI

FastAPI is ASGI-native (built on Starlette) and async by design — an `async def` endpoint genuinely runs
concurrently with every other in-flight request on the same worker, the real version of what Flask's
async shim only approximates for one handler at a time. It leans heavily on type hints: request/response
schemas are Pydantic models, validated automatically, with interactive docs (Swagger/ReDoc) generated
from the same type hints for free.

**Dependency injection** — `Depends(...)` — is how request-scoped resources (a DB session, the current
user, config) get built once per request and handed to any handler that declares them as a parameter:

```python
from fastapi import Depends, FastAPI

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db          # a generator dependency -- FastAPI runs cleanup after the request
    finally:
        db.close()

@app.get("/items/")
def read_items(db=Depends(get_db)):
    return db.query(Item).all()
```

A `yield`-based dependency like `get_db` is exactly a generator being used for its `.close()`-on-cleanup
behavior — the same mechanism behind `@contextlib.contextmanager`, covered from first principles in
[generators-and-coroutines.md §5](generators-and-coroutines.md).

**Pydantic validation** — request and response bodies are declared as `BaseModel` subclasses; FastAPI
validates incoming JSON against the model automatically and returns a structured `422` on mismatch,
before your handler code ever runs:

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float
    tax: float | None = None

@app.post("/items/")
async def create_item(item: Item):
    return {"name": item.name, "total": item.price + (item.tax or 0)}
```

**Background tasks** run after the response has already been sent — for work the caller shouldn't have
to wait on (an email, a log write) but that isn't important enough to need a real task queue:

```python
from fastapi import BackgroundTasks

def write_log(message: str):
    with open("log.txt", "a") as f:
        f.write(message + "\n")

@app.post("/notify/")
async def notify(background_tasks: BackgroundTasks, email: str):
    background_tasks.add_task(write_log, f"notified {email}")
    return {"status": "queued"}
```

**Middleware** wraps every request/response — logging, timing, or auth that applies uniformly:

```python
import time

@app.middleware("http")
async def add_timing_header(request, call_next):
    start = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(time.time() - start)
    return response
```

**CORS** is one of the built-in middlewares, configured declaratively rather than hand-rolled per route:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],   # never "*" with allow_credentials=True
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Auth patterns** — the common shape is OAuth2 with a bearer token, validated inside a dependency that
every protected route pulls in via `Depends`, so the check is written once:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    user = decode_and_look_up(token)             # your own JWT/session validation
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    return user

@app.get("/me")
def read_me(user=Depends(get_current_user)):
    return user
```

**WebSockets** are a first-class route type — a connection-manager object tracking active sockets is the
standard shape for anything beyond a single client:

```python
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active = []
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)
    async def broadcast(self, message: str):
        for ws in self.active:
            await ws.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/chat")
async def chat(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

This is directly relevant to the strongest reported 2026 design signal — "design a scalable real-time
chat system with delivery guarantees" — see
[realtime-chat-delivery-guarantees.md](../15-system-design/realtime-chat-delivery-guarantees.md) for the
full design; this is what the WebSocket layer of that design would actually look like in code.

---

## 3 · Django ORM — `select_related` vs `prefetch_related`, and the N+1 problem

**The N+1 query problem, generally**: fetch N parent rows with one query, then loop over them accessing
a related object per row — and if that access isn't already loaded, each iteration fires its own query.
One query becomes `1 + N`. This is a genuinely common interview question, not Django-specific in
substance (every ORM has this failure mode), but Django's two named fixes are the concrete vocabulary
worth having exact:

```python
# N+1: one query for the books, then one MORE query per book to fetch its author
books = Book.objects.all()
for book in books:
    print(book.title, book.author.name)     # book.author is a separate query, EVERY iteration
```

**`select_related`** — for single-valued relationships (a foreign key or one-to-one) — fetches the
related object in the **same query**, via a SQL `JOIN`:

```python
books = Book.objects.select_related("author").all()   # ONE query, a JOIN
for book in books:
    print(book.title, book.author.name)                 # no extra query -- already loaded
```

**`prefetch_related`** — for multi-valued relationships (many-to-many, or the reverse side of a foreign
key) — can't be joined into one row-per-result the way a single-valued relationship can, so it issues a
**second, separate query** for all the related objects across every parent at once, then joins them in
Python:

```python
books = Book.objects.prefetch_related("authors").all()   # TWO queries total, not N+1
for book in books:
    print(book.title, [a.name for a in book.authors.all()])   # already loaded, no extra query
```

The choice is mechanical, not a judgment call: single-valued relationship (FK, one-to-one) →
`select_related`, one JOIN; multi-valued (M2M, reverse FK) → `prefetch_related`, a second query joined in
Python because a SQL JOIN would multiply each parent row once per related row instead of keeping one row
per parent.

**Migrations** are Django's versioned, ordered record of schema changes — each `makemigrations` run
produces a migration file describing the diff from the previous state (add a column, alter a field), and
`migrate` applies whichever migrations haven't run yet against the actual database. They're checked into
version control alongside the models they describe, specifically so the schema's history is
reconstructable and every environment can be brought to the same state by replaying the same ordered
sequence.

---

## 4 · Rate limiting at the app layer

The algorithms — token bucket, sliding window, fixed window and its boundary flaw — are fully worked in
[15-system-design/rate-limiter.md](../15-system-design/rate-limiter.md); this section is only about where
that logic plugs into a web framework. The common shape is middleware: intercept the request before it
reaches a handler, check and update a shared counter (typically Redis, matching
[lyft-architecture.md](../15-system-design/lyft-architecture.md)'s own "Redis config at both edge and
service-mesh layers"), and reject with `429` if the limit's exceeded:

```python
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    key = request.client.host
    if not await token_bucket.allow(key):        # the algorithm itself lives in rate-limiter.md
        raise HTTPException(status_code=429, detail="rate limit exceeded")
    return await call_next(request)
```

Flask's equivalent is a `before_request` hook registered on the app or a blueprint, doing the same
check-then-reject before the view function runs. Either way, the framework's job is only routing the
request through the check at the right point — the actual algorithm and its memory/accuracy trade-offs
are the substance, and that substance lives in `rate-limiter.md`, not here.

---

## 5 · Testing web apps

All three frameworks' testing tools are built to work from a plain `unittest.TestCase` — no `pytest`
required, which lines up directly with this program's own testing convention
([testing-with-unittest.md](testing-with-unittest.md)):

- **Flask**: `app.test_client()` gives an in-process fake client — no real socket, no real server — that
  calls routes directly and returns real `Response` objects to assert on.
- **FastAPI**: `fastapi.testclient.TestClient` (built on `httpx`, wrapping Starlette's own test client)
  does the same for an ASGI app, sync-looking calls even against `async def` endpoints.
- **Django**: `django.test.TestCase` **is** a `unittest.TestCase` subclass directly, with database
  fixtures and transaction rollback per test layered on top.

```python
from myapp import create_app

class TestUsersAPI(unittest.TestCase):
    def setUp(self):
        self.client = create_app(config={"TESTING": True}).test_client()

    def test_get_missing_user_is_404(self):
        response = self.client.get("/users/999")
        self.assertEqual(response.status_code, 404)
```

The app factory pattern from §1 is exactly what makes `setUp` above possible — a fresh, independently
configured app per test, with no shared module-level state leaking between tests.

---

## 6 · Deployment — brief

Full treatment, containerizing, worker models, health probes, graceful shutdown, is in
[deploying-python-services.md](../14-cloud-and-infrastructure/deploying-python-services.md) — not
repeated here. The one framework-specific fact worth having ready: **Flask and Django run under gunicorn**
(WSGI, sync/gthread/gevent worker classes), while **FastAPI runs under uvicorn** (ASGI) — commonly as
`gunicorn`-managed `UvicornWorker` processes, so gunicorn still handles process management and restarts
while uvicorn runs the actual async event loop inside each worker.

---

## Interview questions

1. **Why does this program lead with Flask instead of FastAPI, given FastAPI is the more modern choice
   for a new API?** Lyft's own Python APIs are built on Flask — it's named directly in their architecture
   — so fluency with Flask specifically is a checkable signal of engagement with their real stack in a
   design round, independent of which framework is technically newer or more feature-rich.

2. **What does the Flask application factory pattern (`create_app()`) buy you over a module-level
   `app = Flask(__name__)`?** Fresh, independently configured app instances per test instead of one
   shared global; config as a constructor argument instead of import-time branching across environments;
   and no import-time side effects, which matters once more than one entry point (server, CLI, tests)
   needs the app.

3. **Flask 2.0+ supports `async def` view functions. Does that make Flask an async framework like
   FastAPI?** No — it's a compatibility shim that runs one event loop per request inside that one
   handler, letting you `await` something inside it. It doesn't change Flask's underlying WSGI worker
   model: a worker still handles one request fully before it's free for the next one, unlike a genuinely
   ASGI framework where many requests share a worker's event loop concurrently.

4. **[Reported at Lyft, as the caller's-side counterpart]** How would you rate-limit a FastAPI (or
   Flask) app at the application layer, and what's the actual mechanism doing the work?** Middleware (or
   a `before_request` hook in Flask) intercepting every request before it reaches a handler, checking and
   updating a counter in a shared store (typically Redis, for correctness across more than one app
   instance) using one of the algorithms in
   [rate-limiter.md](../15-system-design/rate-limiter.md) — token bucket for a bursty-client-friendly
   limit, sliding window counter as the usual production default. The framework's only job is routing the
   request through that check at the right point.

5. **A loop over a Django queryset accessing `book.author.name` fires one query per book. What's this
   called, and what's the one-line fix for a single-valued relationship like this?** The N+1 query
   problem — one query for the parent rows, then N more for the related object each iteration touches.
   `Book.objects.select_related("author")` fixes it for a foreign key/one-to-one relationship by pulling
   the related row into the same query via a SQL JOIN.

6. **Why doesn't `select_related` work for a many-to-many field the same way it does for a foreign
   key?** A SQL JOIN across a multi-valued relationship multiplies each parent row once per related row,
   which breaks "one row per parent." `prefetch_related` instead issues one additional query for all the
   related rows across every parent at once, and joins them in Python, avoiding both the row multiplication
   and the N+1 pattern.

7. **All three frameworks' test tools are designed to work with plain `unittest`. Why does that matter
   for this program specifically?** The target machine has no `pytest` installed, and this program's
   testing convention throughout is `python3 -m unittest` — Django's `TestCase` literally is a
   `unittest.TestCase` subclass, and both Flask's `test_client()` and FastAPI's `TestClient` are designed
   to be called from inside one, so nothing about testing a web app in this stack requires stepping
   outside that convention.

8. **What's the actual difference in how Flask/Django and FastAPI get deployed?** Flask and Django are
   WSGI and run under gunicorn's own worker classes (sync, gthread, gevent). FastAPI is ASGI and runs
   under uvicorn — typically as gunicorn-managed `UvicornWorker` processes, so gunicorn still handles
   process supervision while uvicorn runs the actual event loop inside each worker. Full detail in
   [deploying-python-services.md §2](../14-cloud-and-infrastructure/deploying-python-services.md).
