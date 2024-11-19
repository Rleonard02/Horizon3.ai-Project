# myproject/webhook-creator/app.py

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import requests
import os
import secrets

app = FastAPI()

# Retrieve AUTH_TOKEN from environment variables
AUTH_TOKEN = os.environ.get("AUTH_TOKEN")

if not AUTH_TOKEN:
    raise RuntimeError("AUTH_TOKEN is not set in environment variables")

@app.post("/create-webhook")
async def create_webhook(request: Request):
    data = await request.json()

    token = request.headers.get("Authorization")

    if token != f"Bearer {AUTH_TOKEN}":
        raise HTTPException(status_code=403, detail="Forbidden: Invalid token")

    repo_url = data.get('repo_url')
    access_token = data.get('access_token')

    if not repo_url or not access_token:
        raise HTTPException(status_code=400, detail="Missing parameters")

    # Extract owner and repo from repo_url
    try:
        owner_repo = repo_url.rstrip('/').split('github.com/')[1]
        owner, repo = owner_repo.split('/')
    except (IndexError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid repository URL")

    # Generate a secret for the webhook
    webhook_secret = secrets.token_hex(20)

    # Store the secret in the shared CodeQL analysis directory
    secret_path = '/shared/codeql_analysis/secret.txt'
    os.makedirs(os.path.dirname(secret_path), exist_ok=True)
    with open(secret_path, 'w') as f:
        f.write(webhook_secret)

    # Get the webhook URL from environment variable
    webhook_url = os.environ.get('WEBHOOK_URL')
    if not webhook_url:
        raise HTTPException(status_code=500, detail="Webhook URL not configured")

    # Prepare the payload for GitHub API
    headers = {
        'Authorization': f'token {access_token}',
        'Accept': 'application/vnd.github+json'
    }
    payload = {
        'name': 'web',
        'config': {
            'url': f'{webhook_url}',
            'content_type': 'json',
            'secret': webhook_secret,
            'insecure_ssl': '0'
        },
        'events': ['push'],
        'active': True
    }

    # Create the webhook via GitHub API
    response = requests.post(
        f'https://api.github.com/repos/{owner}/{repo}/hooks',
        headers=headers,
        json=payload
    )

    if response.status_code == 201:
        return JSONResponse(content={'message': 'Webhook created successfully'}, status_code=201)
    else:
        return JSONResponse(content={'error': response.json()}, status_code=response.status_code)
