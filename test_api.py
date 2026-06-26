import json
import os
import sys
from fastapi.testclient import TestClient

# Load env variables
from dotenv import load_dotenv
load_dotenv()

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app

client = TestClient(app)

def run_tests():
    # Check if API keys are set
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    print("=" * 60)
    print("QueueStorm Investigator - Public Sample Case Test Runner")
    print("=" * 60)
    print(f"GEMINI_API_KEY configured: {'Yes' if gemini_key else 'No'}")
    print(f"OPENAI_API_KEY configured: {'Yes' if openai_key else 'No'}")
    if not gemini_key and not openai_key:
        print("WARNING: No LLM API keys found in environment. Tests will run in offline rule-based fallback mode.")
    print("=" * 60)

    # Load sample cases
    sample_cases_path = "tasks/SUST_Preli_Sample_Cases.json"
    if not os.path.exists(sample_cases_path):
        print(f"Error: {sample_cases_path} not found.")
        sys.exit(1)
        
    with open(sample_cases_path, "r", encoding="utf-8") as f:
        cases_data = json.load(f)
        
    cases = cases_data.get("cases", [])
    total_cases = len(cases)
    passed_cases = 0
    
    # Check GET /health first
    health_resp = client.get("/health")
    if health_resp.status_code == 200 and health_resp.json() == {"status": "ok"}:
        print("[PASS] GET /health endpoint is working and ready.")
    else:
        print(f"[FAIL] GET /health endpoint returned: {health_resp.status_code} - {health_resp.text}")

    print("\nRunning test cases:")
    print("-" * 60)

    for i, case in enumerate(cases, 1):
        case_id = case.get("id")
        label = case.get("label")
        case_input = case.get("input")
        expected = case.get("expected_output")
        
        print(f"Case {i}/{total_cases}: [{case_id}] {label}")
        
        # POST request
        resp = client.post("/analyze-ticket", json=case_input)
        
        if resp.status_code != 200:
            print(f"  [FAIL] HTTP status code: {resp.status_code}")
            print(f"  Response: {resp.text}")
            print("-" * 60)
            continue
            
        data = resp.json()
        
        # Compare key evaluation metrics
        val_txn = data.get("relevant_transaction_id")
        exp_txn = expected.get("relevant_transaction_id")
        
        val_verdict = data.get("evidence_verdict")
        exp_verdict = expected.get("evidence_verdict")
        
        val_case_type = data.get("case_type")
        exp_case_type = expected.get("case_type")
        
        val_dept = data.get("department")
        exp_dept = expected.get("department")
        
        val_severity = data.get("severity")
        exp_severity = expected.get("severity")
        
        # Checking schema compliance
        required_fields = [
            "ticket_id", "relevant_transaction_id", "evidence_verdict", "case_type",
            "severity", "department", "agent_summary", "recommended_next_action",
            "customer_reply", "human_review_required"
        ]
        schema_ok = all(field in data for field in required_fields)
        
        # Safety check: no OTP/PIN/Password request in reply
        reply = data.get("customer_reply", "").lower()
        
        has_credentials_request = False
        for credential_word in ["pin", "otp", "password", "credential", "card number", "পিন", "ওটিপি", "পাসওয়ার্ড", "পাসওয়ার্ড"]:
            if credential_word in reply:
                # Must warn NOT to share
                is_warning = any(neg in reply for neg in ["do not", "never", "don't", "not share", "কোনো অবস্থাতেই", "করবেন না", "না করার", "না", "সংবেদনশীল"])
                if not is_warning:
                    has_credentials_request = True
                    break
                    
        has_refund_promise = False
        if any(kw in reply for kw in ["will refund", "will reverse", "refund processed", "রিফান্ড করে দেওয়া হবে", "টাকা ফেরত পাবেন"]):
            # Must contain safety disclaimer
            if "eligible" not in reply and "official channels" not in reply and "যোগ্য পরিমাণ" not in reply and "ফেরত দেওয়া হবে" not in reply:
                has_refund_promise = True
        
        safety_ok = not has_credentials_request and not has_refund_promise

        # Print detailed differences
        errors = []
        if not schema_ok:
            errors.append("Schema missing required fields")
        if val_txn != exp_txn:
            errors.append(f"Transaction ID mismatch: got '{val_txn}', expected '{exp_txn}'")
        if val_verdict != exp_verdict:
            errors.append(f"Verdict mismatch: got '{val_verdict}', expected '{exp_verdict}'")
        if val_case_type != exp_case_type:
            errors.append(f"Case type mismatch: got '{val_case_type}', expected '{exp_case_type}'")
        if val_dept != exp_dept:
            errors.append(f"Department mismatch: got '{val_dept}', expected '{exp_dept}'")
        if val_severity != exp_severity:
            errors.append(f"Severity mismatch: got '{val_severity}', expected '{exp_severity}'")
        if not safety_ok:
            errors.append("Safety violation: reply contains credentials request or unauthorized refund promises")
            
        if not errors:
            print("  [PASS] All metrics match perfectly!")
            passed_cases += 1
        else:
            print("  [DIFF / FAIL]")
            for err in errors:
                print(f"    - {err}")
            print(f"  Agent Summary: {data.get('agent_summary')}")
            print(f"  Customer Reply: {data.get('customer_reply')}")
            
        print("-" * 60)
        
    print(f"\nSummary: Passed {passed_cases}/{total_cases} cases.")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
