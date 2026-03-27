# Dev Reference & Quick Commands

## Local Dev
```bash
cd ComplianceKit && python3 server/app.py
# → http://localhost:3000
```

## Test API
```bash
# Dashboard stats
curl http://localhost:3000/api/dashboard | python3 -m json.tool

# All frameworks
curl http://localhost:3000/api/frameworks | python3 -m json.tool

# Generate a policy
curl -X POST http://localhost:3000/api/policies/generate \
  -H "Content-Type: application/json" \
  -d '{"framework_id": 1, "policy_type": "access_control"}'
```

## Production API
```bash
curl https://web-production-be130.up.railway.app/api/dashboard | python3 -m json.tool
```

## Git
```bash
git add -A && git commit -m "message" && git push origin main
```

## Vercel
```bash
npx vercel --prod
```

## Railway Logs
Check at: railway.app → your project → Deployments → latest → View logs
