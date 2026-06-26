import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from models import TicketRequest, AnalysisResponse
from analyzer import analyze_ticket

app = FastAPI(title="QueueStorm Investigator API")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("queuestorm.main")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    logger.warning(f"Validation error for request: {errors}")
    
    # Check if the validation error is due to missing required fields
    is_missing = any(err.get("type") == "missing" for err in errors)
    
    # Check if JSON decode error (malformed JSON)
    is_json_decode_error = any("json_invalid" in err.get("type", "") for err in errors)
    
    if is_missing or is_json_decode_error:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Malformed input: missing required fields or invalid JSON format."}
        )
    
    # Check for empty complaint or invalid field values (semantic invalidity)
    for err in errors:
        loc = err.get("loc", [])
        if "complaint" in loc:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"detail": "Semantically invalid input: complaint text cannot be empty."}
            )
            
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": f"Semantically invalid input details: {errors}"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception occurred: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Secrets, tokens, and stack traces are suppressed."}
    )

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/analyze-ticket", response_model=AnalysisResponse)
async def analyze_ticket_endpoint(request: TicketRequest):
    # Extra validation for empty/whitespace complaint
    if not request.complaint or not request.complaint.strip():
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Semantically invalid input: complaint text cannot be empty or whitespace."}
        )
        
    response = analyze_ticket(request)
    return response
