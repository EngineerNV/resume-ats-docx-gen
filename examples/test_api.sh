#!/bin/bash
# Test script for the FastAPI server endpoints

echo "======================================================================"
echo "FastAPI Server Test Script"
echo "======================================================================"
echo ""

# Check if server is running
echo "Testing health check endpoint..."
echo "GET http://localhost:8000/"
echo "----------------------------------------------------------------------"
response=$(curl -s http://localhost:8000/ 2>&1)
if [ $? -eq 0 ]; then
    echo "Response: $response"
    echo "✅ Health check passed"
else
    echo "❌ Server is not running!"
    echo "Start the server with: resume-api"
    exit 1
fi
echo ""

# Create a temp file with sample resume text
RESUME_TEXT="John Doe
Email: john.doe@example.com
Location: San Francisco, CA

EXPERIENCE
Software Engineer at Tech Corp (2020-Present)
- Built scalable microservices
- Led team of 4 engineers

EDUCATION
B.S. Computer Science, UC Berkeley (2018)"

echo "Testing JSON workflow endpoint (resume improvement mode)..."
echo "POST http://localhost:8000/api/workflow/json"
echo "----------------------------------------------------------------------"
echo "Note: This requires OPENAI_API_KEY in .env file"
echo ""

# Uncomment to test JSON endpoint
# curl -X POST http://localhost:8000/api/workflow/json \
#   -F "mode=resume" \
#   -F "resumeText=$RESUME_TEXT" \
#   -H "Accept: application/json" | jq .

echo "To test the JSON endpoint, uncomment the curl command in this script"
echo ""

echo "======================================================================"
echo "Manual Testing Commands"
echo "======================================================================"
echo ""
echo "Test health check:"
echo "  curl http://localhost:8000/"
echo ""
echo "Test JSON workflow (requires API key):"
echo "  curl -X POST http://localhost:8000/api/workflow/json \\"
echo "    -F 'mode=resume' \\"
echo "    -F 'resumeText=Your resume text here...' | jq ."
echo ""
echo "Test DOCX generation (requires API key):"
echo "  curl -X POST http://localhost:8000/api/workflow/docx \\"
echo "    -F 'mode=resume' \\"
echo "    -F 'resumeText=Your resume text here...' \\"
echo "    -o resume.docx"
echo ""
echo "Interactive API docs:"
echo "  http://localhost:8000/docs"
echo ""
