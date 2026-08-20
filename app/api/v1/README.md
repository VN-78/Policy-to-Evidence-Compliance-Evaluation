# API Version 1 (`app/api/v1/`)

This directory contains version 1 API endpoints and routers. Keeping routers version-isolated prevents breaking changes when API behavior is updated in the future.

## 📂 Files

* **`__init__.py`**: Combines and registers all version 1 routes onto the `v1_router` using `include_router()`.
* **`users.py`**: Defines `/users` related endpoints (creation, fetching, etc.).

## 🚀 Connecting to the Main Application

Version 1 routes are registered on a central `v1_router` which is then included in [`app/main.py`](file:///home/vn-78/Projects/code/fastapi-base-template/app/main.py):

```python
# app/api/v1/__init__.py
from fastapi import APIRouter
from app.api.v1.users import router as users_router

v1_router = APIRouter()
v1_router.include_router(users_router, prefix="/users", tags=["Users"])
```

```python
# app/main.py
app.include_router(v1_router, prefix="/api/v1")
```

This prefixes all version 1 endpoints with `/api/v1` (e.g. `/api/v1/users/`).

## 🛠️ Adding a New Endpoint (e.g., Products)

To add a new endpoint, follow these steps:

1. Create your route file: `app/api/v1/products.py`
   ```python
   from fastapi import APIRouter

   router = APIRouter()

   @router.get("/")
   def list_products():
       return []
   ```
2. Import and register the new router in [`app/api/v1/__init__.py`](file:///home/vn-78/Projects/code/fastapi-base-template/app/api/v1/__init__.py):
   ```python
   from app.api.v1.products import router as products_router

   v1_router.include_router(products_router, prefix="/products", tags=["Products"])
   ```
