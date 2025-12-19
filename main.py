from fastapi import FastAPI
from transport.http.v1.routes.ping import router as ping_router
from transport.http.v1.routes.echo import router as echo_router
from transport.http.v1.routes.users import router as users_router

app = FastAPI(
    title="Clean Architecture API",
    description="API structured with Clean Architecture principles",
    version="1.0.0"
)

app.include_router(ping_router, prefix="/api/v1")
app.include_router(echo_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
