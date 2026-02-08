#!/bin/bash
# Quick test script for Why Energy Stack MVP
# Usage: ./test-why-stack.sh

set -e

echo "🚀 Why Energy Stack - Quick Test Script"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the correct directory
if [ ! -d "backend" ] || [ ! -d "mobile" ]; then
    echo -e "${RED}❌ Error: Must be run from Pulse root directory${NC}"
    exit 1
fi

# Function to check if backend is running
check_backend() {
    echo -e "${YELLOW}🔍 Checking if backend is running...${NC}"
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is running${NC}"
        return 0
    else
        echo -e "${RED}❌ Backend is not running${NC}"
        echo -e "${YELLOW}   Start it with: cd backend && python api_server.py${NC}"
        return 1
    fi
}

# Function to test the explain endpoint
test_explain_endpoint() {
    echo ""
    echo -e "${YELLOW}🧪 Testing /api/energy/explain endpoint...${NC}"
    
    # You need to replace this with a real user_id and JWT token
    USER_ID="c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd"
    
    echo -e "${YELLOW}   User ID: ${USER_ID}${NC}"
    echo -e "${YELLOW}   Note: You need a valid JWT token to test this endpoint${NC}"
    echo ""
    echo -e "${YELLOW}   curl -X GET \"http://localhost:8000/api/energy/explain/${USER_ID}?date=2026-02-01\" \\${NC}"
    echo -e "${YELLOW}     -H \"Authorization: Bearer YOUR_JWT_TOKEN\"${NC}"
    echo ""
}

# Function to run backend tests
test_backend() {
    echo ""
    echo -e "${YELLOW}🧪 Running backend tests...${NC}"
    
    cd backend
    
    # Check if test file exists
    if [ ! -f "test_explain_service.py" ]; then
        echo -e "${RED}❌ test_explain_service.py not found${NC}"
        cd ..
        return 1
    fi
    
    # Run tests
    echo -e "${YELLOW}   Running: python test_explain_service.py${NC}"
    python test_explain_service.py
    
    cd ..
    
    echo -e "${GREEN}✅ Backend tests completed${NC}"
}

# Function to check frontend dependencies
check_frontend_deps() {
    echo ""
    echo -e "${YELLOW}🔍 Checking frontend dependencies...${NC}"
    
    cd mobile
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${RED}❌ node_modules not found${NC}"
        echo -e "${YELLOW}   Run: npm install${NC}"
        cd ..
        return 1
    fi
    
    # Check critical packages
    PACKAGES=("expo-blur" "react-native-reanimated" "@tanstack/react-query")
    ALL_PRESENT=true
    
    for package in "${PACKAGES[@]}"; do
        if [ ! -d "node_modules/$package" ]; then
            echo -e "${RED}❌ $package not found${NC}"
            ALL_PRESENT=false
        else
            echo -e "${GREEN}✅ $package installed${NC}"
        fi
    done
    
    cd ..
    
    if [ "$ALL_PRESENT" = true ]; then
        echo -e "${GREEN}✅ All frontend dependencies present${NC}"
        return 0
    else
        echo -e "${YELLOW}   Run: cd mobile && npx expo install --fix${NC}"
        return 1
    fi
}

# Function to run expo doctor
run_expo_doctor() {
    echo ""
    echo -e "${YELLOW}🩺 Running expo doctor...${NC}"
    
    cd mobile
    npx expo-doctor
    cd ..
    
    echo -e "${GREEN}✅ Expo doctor completed${NC}"
}

# Function to list created files
list_files() {
    echo ""
    echo -e "${YELLOW}📁 Files created for Why Energy Stack:${NC}"
    echo ""
    echo -e "${GREEN}Backend:${NC}"
    echo "  ✅ backend/explain_service.py"
    echo "  ✅ backend/test_explain_service.py"
    echo "  ✅ backend/example_explain_response.json"
    echo "  ✏️  backend/api_server.py (modified)"
    echo ""
    echo -e "${GREEN}Frontend:${NC}"
    echo "  ✅ mobile/src/hooks/useEnergyExplanation.ts"
    echo "  ✅ mobile/src/components/WhyEnergyStack.tsx"
    echo "  ✏️  mobile/app/(tabs)/energie.tsx (modified)"
    echo ""
    echo -e "${GREEN}Documentation:${NC}"
    echo "  ✅ mobile/WHY_ENERGY_STACK_MVP.md"
    echo "  ✅ WHY_ENERGY_STACK_IMPLEMENTATION.md"
    echo "  ✅ test-why-stack.sh (this file)"
    echo ""
}

# Main execution
main() {
    echo ""
    echo -e "${YELLOW}1️⃣  Listing created files...${NC}"
    list_files
    
    echo ""
    echo -e "${YELLOW}2️⃣  Checking backend...${NC}"
    if check_backend; then
        test_explain_endpoint
    fi
    
    echo ""
    echo -e "${YELLOW}3️⃣  Checking frontend dependencies...${NC}"
    check_frontend_deps
    
    echo ""
    echo "========================================"
    echo -e "${GREEN}✅ Quick test completed!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Start backend: cd backend && python api_server.py"
    echo "  2. Start mobile: cd mobile && npx expo start --clear"
    echo "  3. Navigate to 'Énergie' tab in the app"
    echo "  4. Scroll down to see the Why Energy Stack"
    echo ""
    echo -e "${YELLOW}To run backend tests:${NC}"
    echo "  cd backend && python test_explain_service.py"
    echo ""
    echo -e "${YELLOW}To run expo doctor:${NC}"
    echo "  cd mobile && npx expo-doctor"
    echo ""
}

# Run main
main
