# Traditional Architecture Guide (Non-Agentic Features)

> **Scope**: Standard web features using layered architecture (CRUD, business logic, integrations)

**Flow**: `Client → Route → Controller → Service → Model/3rd Party → Response`

---

## Layered Architecture Pattern

**Layers**:
1. **Route Layer** (`app/api/routes/`): HTTP endpoint definitions
2. **Controller Layer** (`app/controllers/`): Request/response handling, validation
3. **Service Layer** (`app/services/`): Business logic, orchestration
4. **Model Layer** (`app/models/`): Database models, schemas
5. **External Layer**: 3rd party APIs, external services

---

## Core Principles

### 1. Separation of Concerns
**Rule**: Each layer has ONE responsibility. No layer does another's job.

**Layer Responsibilities**:
- **Routes**: Define endpoints, bind to controllers
- **Controllers**: Validate input, call services, format response
- **Services**: Implement business logic, coordinate operations
- **Models**: Data structure, database queries

**Red Flags**:
- ❌ Business logic in controllers
- ❌ HTTP handling in services  
- ❌ Database queries in controllers
- ❌ Response formatting in services

### 2. Dependency Direction
**Rule**: Dependencies flow inward (outer layers depend on inner).

```
Routes → Controllers → Services → Models
  ↓         ↓            ↓         ↓
(HTTP)   (Validate)  (Logic)   (Data)
```

**Allowed (correct direction)**:
- ✅ Controllers import Services
- ✅ Services import Models
- ✅ Services import other Services

**Never reverse (wrong direction)**:
- ❌ Models import from Services
- ❌ Services import from Controllers
- ❌ Models import from Controllers

### 3. Reusability
**Rule**: Services are reusable by multiple controllers/routes.

**Example**:
```python
# ✅ CORRECT: Reusable service
class UserService:
    def create_user(self, data): ...
    def get_user(self, user_id): ...

# Controllers use the service
class UserController:
    def __init__(self):
        self.user_service = UserService()
```

### 4. Single Source of Truth
**Rule**: One service per domain/resource. No duplicate logic.

**Examples**:
- User operations → `UserService`
- Payment processing → `PaymentService`
- Notifications → `NotificationService`

### 5. Error Handling
**Rule**: Raise exceptions in services, handle in controllers.

```python
# ✅ Service raises
class UserService:
    def get_user(self, user_id):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException(f"User {user_id} not found")
        return user

# ✅ Controller handles
class UserController:
    def get_user(self, user_id):
        try:
            return self.user_service.get_user(user_id)
        except NotFoundException as e:
            return JSONResponse(status_code=404, content={"error": str(e)})
```

---

## Architecture Patterns

### Pattern 1: Controller-Service Pattern
**Every endpoint follows**:
1. **Controller**: Receive request, validate
2. **Service**: Execute business logic
3. **Controller**: Return formatted response

```python
# Route
@router.post("/users")
async def create_user(data: UserCreate):
    return await UserController().create(data)

# Controller
class UserController:
    def __init__(self):
        self.user_service = UserService()
    
    async def create(self, data: UserCreate):
        try:
            user = await self.user_service.create_user(data)
            return {"success": True, "data": user}
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))

# Service
class UserService:
    async def create_user(self, data: UserCreate):
        user = User(**data.dict())
        db.add(user)
        await db.commit()
        return user
```

### Pattern 2: Service Composition
**When one feature needs multiple services**:

```python
class OrderService:
    def __init__(self):
        self.user_service = UserService()
        self.payment_service = PaymentService()
        self.notification_service = NotificationService()
    
    def create_order(self, order_data):
        # Orchestrate multiple services
        user = self.user_service.get_user(order_data.user_id)
        payment = self.payment_service.process(order_data.payment)
        order = self._save_order(order_data, payment)
        self.notification_service.send_order_confirmation(user, order)
        return order
```

### Pattern 3: Repository Pattern (Optional)
**For complex data access**:

```python
class UserRepository:
    def find_by_id(self, user_id): ...
    def find_by_email(self, email): ...
    def save(self, user): ...

class UserService:
    def __init__(self):
        self.user_repo = UserRepository()
    
    def get_user(self, user_id):
        return self.user_repo.find_by_id(user_id)
```

---

## Decision Frameworks

### When to Create New Service?
Ask:
1. Is this a distinct business domain/resource? ✓
2. Will multiple controllers need this logic? ✓
3. Is the logic complex enough to warrant separation? ✓
4. Does it have its own data model? ✓

All YES → Create new service | Otherwise → Add to existing service

### When to Create New Controller?
Ask:
1. Is this a new API resource/endpoint group? ✓
2. Does it have distinct request/response patterns? ✓
3. Would it make routes file cleaner? ✓

Most YES → Create new controller | Otherwise → Add to existing

### When to Call External APIs?
**Always in service layer**, never in controllers.

```python
# ✅ CORRECT: Service calls external API
class PaymentService:
    def process_payment(self, data):
        response = requests.post(STRIPE_API_URL, data)
        return response.json()

# ❌ WRONG: Controller calling external API
class PaymentController:
    def process(self, data):
        response = requests.post(STRIPE_API_URL, data)  # NO!
```

---

## Anti-Patterns

| ❌ Never | ✅ Instead |
|---------|----------|
| Business logic in controllers | Move to services |
| Database queries in controllers | Use services/repositories |
| HTTP handling in services | Services return data, controllers handle HTTP |
| Duplicate service logic | Create shared service method |
| Fat controllers | Thin controllers, fat services |
| Services depending on request objects | Pass only needed data |
| Circular service dependencies | Refactor or introduce mediator |

---

## File Organization

```
app/
├── api/
│   └── routes/
│       ├── user_routes.py       # User endpoints
│       ├── order_routes.py      # Order endpoints
│       └── payment_routes.py    # Payment endpoints
├── controllers/
│   ├── user_controller.py       # User request handling
│   ├── order_controller.py
│   └── payment_controller.py
├── services/
│   ├── user_service.py          # User business logic
│   ├── order_service.py
│   ├── payment_service.py
│   └── notification_service.py
├── models/
│   ├── user.py                  # User database model
│   ├── order.py
│   └── payment.py
└── schemas/
    ├── user_schema.py           # Pydantic schemas
    └── order_schema.py
```

---

## Testing Requirements

**Coverage Minimums**:
- Unit tests: 70% for services
- Integration tests: Critical business flows
- API tests: All endpoints

**Test Structure**:
```
tests/
├── test_services/
│   ├── test_user_service.py
│   └── test_order_service.py
├── test_controllers/
│   ├── test_user_controller.py
│   └── test_order_controller.py
└── test_api/
    ├── test_user_endpoints.py
    └── test_order_endpoints.py
```

**Service Test Pattern**:
```python
def test_create_user():
    service = UserService()
    user_data = {"name": "John", "email": "john@example.com"}
    
    user = service.create_user(user_data)
    
    assert user.id is not None
    assert user.name == "John"
    assert user.email == "john@example.com"
```

**API Test Pattern**:
```python
def test_create_user_endpoint(client):
    response = client.post("/users", json={
        "name": "John",
        "email": "john@example.com"
    })
    
    assert response.status_code == 201
    assert response.json()["success"] == True
    assert "id" in response.json()["data"]
```

---

## Self-Check Checklist

**Service Code**:
- [ ] Contains only business logic (no HTTP handling)
- [ ] Reusable by multiple controllers
- [ ] Raises appropriate exceptions
- [ ] No direct database imports (uses models/repositories)
- [ ] All methods have single responsibility
- [ ] Unit tests cover all methods

**Controller Code**:
- [ ] Validates input (Pydantic schemas)
- [ ] Calls services for logic
- [ ] Handles exceptions and returns HTTP responses
- [ ] No business logic or database queries
- [ ] Returns consistent response format

**Route Code**:
- [ ] Clean endpoint definitions
- [ ] Proper HTTP methods (GET, POST, PUT, DELETE)
- [ ] Uses Pydantic models for validation
- [ ] Delegates to controllers

**Testing**:
- [ ] Services have unit tests (mocked dependencies)
- [ ] Controllers have integration tests
- [ ] All endpoints have API tests
- [ ] All tests pass

---

**Related**: See [CONSTITUTION.md](CONSTITUTION.md) for universal principles and [AGENTIC_ARCHITECTURE.md](AGENTIC_ARCHITECTURE.md) for AI features.
