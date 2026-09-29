# PayShield API Error Codes

All business rule violations return a standardized JSON structure with HTTP status 400, 403, 404, or 409 depending on the action:
```json
{
  "error": "RULE_CODE",
  "message": "Human-readable description of the error."
}