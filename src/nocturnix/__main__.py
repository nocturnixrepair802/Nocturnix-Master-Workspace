import uvicorn

uvicorn.run("nocturnix.api.app:create_app", factory=True, host="127.0.0.1", port=8000)
