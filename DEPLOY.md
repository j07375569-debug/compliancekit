# ComplianceKit — Deployment Guide

Total time: ~30 minutes. You need a Railway account, a Vercel account, and a Stripe account.

---

## Step 1: Stripe Setup (10 min)

### 1.1 Get your API keys
1. Go to https://dashboard.stripe.com/apikeys
2. Copy your **Secret key** (starts with `sk_live_` for production, `sk_test_` for testing)

### 1.2 Create your products
1. Go to https://dashboard.stripe.com/products
2. Click **Add product** — create these 3:

| Name | Price | Billing |
|------|-------|---------|
| ComplianceKit Starter | $49.00 | Monthly recurring |
| ComplianceKit Growth | $99.00 | Monthly recurring |
| ComplianceKit Pro | $149.00 | Monthly recurring |

3. After creating each, click on the price and copy the **Price ID** (starts with `price_`)

### 1.3 Set up webhook (do this AFTER Railway deploy in Step 2)
1. Go to https://dashboard.stripe.com/webhooks
2. Click **Add endpoint**
3. URL: `https://your-railway-url.up.railway.app/api/billing/webhook`
4. Select events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
5. Copy the **Signing secret** (starts with `whsec_`)

---

## Step 2: Deploy Backend to Railway (10 min)

### 2.1 Push to GitHub first
```bash
cd ~/Documents/Claude/Projects/k/ComplianceKit
git init
git add .
git commit -m "Initial ComplianceKit deployment"
# Create a new repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/compliancekit.git
git push -u origin main
```

### 2.2 Deploy on Railway
1. Go to https://railway.app → New Project → Deploy from GitHub repo
2. Select your `compliancekit` repo
3. Railway auto-detects Python via `Procfile`

### 2.3 Set environment variables on Railway
In your Railway project → Variables tab, add:

```
PORT=3000
STRIPE_SECRET_KEY=sk_live_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_secret_here
STRIPE_PRICE_STARTER=price_your_starter_id
STRIPE_PRICE_GROWTH=price_your_growth_id
STRIPE_PRICE_PRO=price_your_pro_id
FRONTEND_URL=https://your-app.vercel.app   ← fill in after Step 3
```

4. Railway gives you a URL like `https://compliancekit-production.up.railway.app`
5. **Copy this URL** — you need it for Step 3.
6. Go back and complete Stripe webhook setup (Step 1.3) with this URL.

---

## Step 3: Deploy Frontend to Vercel (5 min)

### 3.1 Update the API URL in index.html
Open `public/index.html` and add this line right before the `<script type="text/babel">` tag:

```html
<script>window.CK_API_URL = 'https://your-railway-url.up.railway.app';</script>
```

Replace with your actual Railway URL.

### 3.2 Commit and deploy
```bash
git add public/index.html
git commit -m "Set production API URL"
git push
```

### 3.3 Deploy on Vercel
1. Go to https://vercel.com → New Project → Import your GitHub repo
2. **Override these settings:**
   - Build Command: *(leave empty)*
   - Output Directory: `public`
3. Click Deploy
4. Vercel gives you a URL like `https://compliancekit.vercel.app`

### 3.4 Update Railway with your Vercel URL
Back in Railway → Variables:
```
FRONTEND_URL=https://compliancekit.vercel.app
```

---

## Step 4: Verify Everything Works

1. Open your Vercel URL
2. Click "Open Dashboard"
3. Go to Billing page
4. Click "Upgrade to Growth" — should redirect to Stripe checkout
5. Use Stripe test card: `4242 4242 4242 4242`, any future date, any CVC
6. After checkout, you should be redirected back to the app

---

## Local Development

```bash
# Set env vars
export STRIPE_SECRET_KEY=sk_test_...
export STRIPE_PRICE_GROWTH=price_...
# etc.

# Run
cd ~/Documents/Claude/Projects/k/ComplianceKit
bash start.sh
```

Or create a `.env` file (copy from `.env.example`) and load it:
```bash
export $(cat .env | xargs) && bash start.sh
```

---

## Troubleshooting

**Stripe checkout fails:** Make sure `STRIPE_SECRET_KEY` and price IDs are set correctly in Railway.

**API calls fail from Vercel:** Check that `window.CK_API_URL` is set in index.html and matches your Railway URL exactly (no trailing slash).

**Webhook not receiving events:** Make sure the Railway URL in Stripe dashboard matches your deployed URL, and `STRIPE_WEBHOOK_SECRET` is set.

**Railway build fails:** Check that `server/database.py` runs without errors. Check Railway build logs.
