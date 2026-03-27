# Prompt: Deploy Frontend to Vercel

## Steps
1. Ensure latest code is committed and pushed to GitHub
2. Run `npx vercel --prod` from project root, OR connect repo at vercel.com/new
3. Vercel config is in vercel.json — serves from public/ directory
4. After deploy: copy the .vercel.app URL
5. Update Railway env var FRONTEND_URL to the Vercel URL
6. Update CORS in app.py if hardcoded (currently allows all origins)
7. Test: visit Vercel URL → landing page loads → click "Start Free Trial" → dashboard loads → API calls succeed

## Validation
- Validator agent: check that all API calls from app.html go to Railway URL, not localhost
- Verify no mixed-content warnings (HTTPS page calling HTTP API)
