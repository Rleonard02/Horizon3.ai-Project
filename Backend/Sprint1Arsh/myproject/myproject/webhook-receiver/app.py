from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib

app = FastAPI()

def verify_signature(payload, signature, secret):
    mac = hmac.new(bytes(secret, 'utf-8'), msg=payload, digestmod=hashlib.sha256)
    expected_signature = 'sha256=' + mac.hexdigest()
    return hmac.compare_digest(expected_signature, signature)

@app.post("/webhook")
async def webhook(request: Request):
    # Load the secret from the shared volume
    try:
        with open('/shared/secret.txt', 'r') as f:
            secret = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Secret not found")

    signature = request.headers.get('X-Hub-Signature-256')
    if not signature:
        raise HTTPException(status_code=403, detail="Signature missing")

    body = await request.body()

    if not verify_signature(body, signature, secret):
        raise HTTPException(status_code=403, detail="Invalid signature")

    print('Webhook received and verified!')
    return {"message": "Webhook received"}
