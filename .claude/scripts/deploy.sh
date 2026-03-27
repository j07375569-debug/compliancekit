#!/bin/bash
# ComplianceKit Deployment Scripts

# === Push to GitHub (auto-deploys backend to Railway) ===
deploy_backend() {
    cd ~/Documents/Claude/Projects/k/ComplianceKit
    git add -A
    git status
    echo "---"
    read -p "Commit message: " msg
    git commit -m "$msg"
    git push origin main
    echo "✓ Pushed. Railway will auto-deploy in ~60 seconds."
}

# === Deploy frontend to Vercel ===
deploy_frontend() {
    cd ~/Documents/Claude/Projects/k/ComplianceKit
    npx vercel --prod
    echo "✓ Deployed. Update FRONTEND_URL in Railway if URL changed."
}

# === Local development ===
dev() {
    cd ~/Documents/Claude/Projects/k/ComplianceKit
    python3 server/app.py
    # Serves at http://localhost:3000
    # Landing: http://localhost:3000/index.html
    # Dashboard: http://localhost:3000/app.html
}

# === Check Railway status ===
check_backend() {
    curl -s https://web-production-be130.up.railway.app/api/dashboard | python3 -m json.tool
}
