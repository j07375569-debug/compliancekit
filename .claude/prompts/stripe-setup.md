# Prompt: Complete Stripe Setup

## What's Done
- Stripe account created
- Test API keys obtained
- 3 products created in Stripe Dashboard
- Backend code handles checkout, portal, webhooks

## What's Left
1. Go to Stripe Dashboard → Products → copy price_XXXXX IDs for all 3 plans
2. Add to Railway env vars: STRIPE_PRICE_STARTER, STRIPE_PRICE_GROWTH, STRIPE_PRICE_PRO
3. In Stripe → Developers → Webhooks → Add endpoint:
   - URL: https://web-production-be130.up.railway.app/api/billing/webhook
   - Events: checkout.session.completed, customer.subscription.updated, customer.subscription.deleted
4. Copy webhook signing secret → add as STRIPE_WEBHOOK_SECRET in Railway
5. Test: visit pricing → click subscribe → should redirect to Stripe Checkout

## Before Launch
- Switch from sk_test_ to sk_live_ keys
- Re-create products/prices in live mode
- Re-register webhook with live endpoint
