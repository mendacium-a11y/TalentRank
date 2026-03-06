echo "=== 1. Create a Job ==="
JOB_RES=$(curl -s -X POST "http://localhost:8000/jobs" -H "Content-Type: application/json" -d '{"jd_text": "We need a Senior Python Engineer"}')
echo $JOB_RES
JOB_ID=$(echo $JOB_RES | grep -o '"job_id":"[^"]*' | cut -d'"' -f4)

echo -e "\n\n=== 2. Upload a Resume ==="
touch mock_resume.pdf
UPLOAD_RES=$(curl -s -X POST "http://localhost:8000/jobs/$JOB_ID/resumes" -F "resumes=@mock_resume.pdf")
echo $UPLOAD_RES

echo -e "\n\n=== 3. Check Grades (Immediate) ==="
curl -s "http://localhost:8000/jobs/$JOB_ID" | jq .

echo -e "\n\n=== Waiting 15s for AI to process in background... ==="
sleep 15

echo -e "\n=== 4. Check Grades (Completed) ==="
curl -s "http://localhost:8000/jobs/$JOB_ID" | jq .
