#!/bin/bash
# Quick validation before pushing to Railway

echo "🔍 Validating Railway deployment setup..."

# Check if all required files exist
echo -e "\n📁 Checking required files:"
files=("Dockerfile" "backend/requirements.txt" "issuer_ed25519.jwk" "backend/app/main.py")
all_good=true

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing!"
        all_good=false
    fi
done

# Check Dockerfile content
echo -e "\n🐳 Checking Dockerfile:"
if grep -q "CMD.*uvicorn" Dockerfile; then
    echo "✅ Dockerfile has uvicorn CMD"
else
    echo "❌ Dockerfile missing uvicorn CMD"
    all_good=false
fi

echo -e "\n📋 Summary:"
if [ "$all_good" = true ]; then
    echo "✅ All checks passed! Ready to deploy to Railway."
    echo -e "\n🚀 Next steps:"
    echo "1. Clear Railway build cache (if needed)"
    echo "2. git add ."
    echo "3. git commit -m 'Railway deployment - simplified approach'"
    echo "4. git push origin main"
else
    echo "❌ Some files are missing. Please fix before deploying."
fi 