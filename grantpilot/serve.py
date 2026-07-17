"""Entry point: python serve.py  (or: uvicorn serve:app --host 0.0.0.0 --port 8000)"""

from grantpilot.server.app import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
