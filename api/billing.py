from fastapi import APIRouter, HTTPException, Request, Header, Depends
from pydantic import BaseModel
import stripe
import config
import core
from typing import Optional
from utils.auth import ClerkUser, get_current_user

router = APIRouter()

class CheckoutRequest(BaseModel):
    tier: str # 'pro' or 'enterprise'

class CheckoutResponse(BaseModel):
    checkout_url: str

class SubscriptionResponse(BaseModel):
    tier: str
    status: str

@router.get("/status", response_model=SubscriptionResponse)
async def get_subscription_status():
    """Retrieve the current fiduciary workspace subscription tier and billing status."""
    try:
        state = core.get_subscription_state()
        return {
            "tier": state.get("tier", "free"),
            "status": state.get("status", "inactive")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/checkout", response_model=CheckoutResponse)
async def create_billing_checkout(body: CheckoutRequest, current_user: ClerkUser = Depends(get_current_user)):
    """Create a Stripe Checkout Session for subscription upgrades, falling back to sandbox mocks."""
    tier = body.tier.lower()
    if tier not in ["pro", "enterprise"]:
        raise HTTPException(status_code=400, detail="Invalid pricing tier. Must be 'pro' or 'enterprise'.")
        
    price_id = "price_1Ppro_mock_id" if tier == "pro" else "price_1Penterprise_mock_id"
    
    # 1. Real Stripe Integration if API key is active
    if config.STRIPE_SECRET_KEY and config.STRIPE_SECRET_KEY != "sk_test_stripe_secret_key_here":
        try:
            stripe.api_key = config.STRIPE_SECRET_KEY
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"http://localhost:3000/dashboard?billing_status=success&tier={tier}",
                cancel_url="http://localhost:3000/dashboard?billing_status=cancel",
            )
            return {"checkout_url": session.url}
        except Exception as e:
            print(f"Stripe API Checkout Error: {e}. Falling back to sandbox simulator...")
            
    # 2. Safe Sandbox Developer fallback
    # Redirects directly back to the dashboard with checkout parameters so the React frontend can simulate success
    mock_url = f"http://localhost:3000/dashboard?mock_checkout_success=true&tier={tier}"
    return {"checkout_url": mock_url}

@router.post("/webhook")
async def stripe_billing_webhook(request: Request, stripe_signature: Optional[str] = Header(None)):
    """Stripe webhook gateway endpoint to sync subscriptions on webhook events."""
    payload = await request.body()
    event = None
    
    if not config.STRIPE_SECRET_KEY or config.STRIPE_SECRET_KEY == "sk_test_stripe_secret_key_here":
        return {"status": "skipped", "message": "Stripe is in mock offline mode."}
        
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, config.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook signature validation failed: {str(e)}")
        
    event_type = event['type']
    
    if event_type in ["checkout.session.completed", "customer.subscription.updated"]:
        session = event['data']['object']
        # Extract metadata or line items to resolve tier
        # Renders standard subscription updates
        metadata = session.get("metadata", {})
        tier = metadata.get("subscription_tier", "pro")
        core.update_subscription_state(tier, "active")
        
    elif event_type == "customer.subscription.deleted":
        core.update_subscription_state("free", "inactive")
        
    return {"status": "success"}

@router.post("/simulate")
async def simulate_billing_upgrade(body: CheckoutRequest):
    """Simulate successful payment billing upgrade locally in development mode."""
    try:
        tier = body.tier.lower()
        if tier not in ["free", "pro", "enterprise"]:
            raise HTTPException(status_code=400, detail="Invalid tier.")
            
        status = "active" if tier != "free" else "inactive"
        core.update_subscription_state(tier, status)
        
        return {
            "success": True,
            "tier": tier,
            "status": status,
            "message": f"Successfully simulated billing checkout for {tier} plan!"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
