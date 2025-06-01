#!/bin/bash
# Quick validation before pushing to Railway

echo "🔍 Validating Railway deployment setup..."

# Check if all required files exist
echo -e "\n📁 Checking required files:"
files=("Dockerfile" "railway_start.py" "backend/requirements.txt" "issuer_ed25519.jwk")
all_good=true

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing!"
        all_good=false
    fi
done

# Check if start.sh is executable
if [ -x "start.sh" ]; then
    echo "✅ start.sh is executable"
else
    echo "⚠️  start.sh is not executable, fixing..."
    chmod +x start.sh
fi

echo -e "\n📋 Summary:"
if [ "$all_good" = true ]; then
    echo "✅ All checks passed! Ready to deploy to Railway."
    echo -e "\n🚀 Next steps:"
    echo "1. git add ."
    echo "2. git commit -m 'Fixed Railway deployment'"
    echo "3. git push origin main"
else
    echo "❌ Some files are missing. Please fix before deploying."
fi 