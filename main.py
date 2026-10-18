
import hashlib
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI()

EMAIL = "24f3004910@ds.study.iitm.ac.in"

TOOL = {
    "name": "solve_challenge",
    "description": "Solve the current exam challenge from HTTP request headers.",
    "inputSchema": {
        "type": "object",
        "properties": {},
    },
}


@app.get("/")
async def health():
    return {"status": "ok", "service": "exam-mcp-server"}


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    # The challenge must be read from the HTTP headers for EACH call.
    body = await request.json()
    method = body.get("method")
    request_id = body.get("id")

    # Notifications have no JSON-RPC id and do not require a response body.
    if method == "notifications/initialized":
        return Response(status_code=202)

    if method == "initialize":
        params = body.get("params") or {}
        requested_version = params.get(
            "protocolVersion", "2025-03-26"
        )

        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": requested_version,
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "exam-mcp-server",
                    "version": "1.0.0"
                }
            }
        })

    if method == "ping":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {}
        })

    if method == "tools/list":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [TOOL]
            }
        })

    if method == "tools/call":
        params = body.get("params") or {}

        if params.get("name") != "solve_challenge":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": "Unknown tool"
                }
            })

        challenge = request.headers.get("x-exam-challenge")

        if challenge is None:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": "Missing X-Exam-Challenge header"
                }
            })

        # Use the header value as received; do not read the challenge
        # from params.arguments or any other JSON body property.
        digest_input = f"{challenge}:{EMAIL}".encode("utf-8")
        answer = hashlib.sha256(digest_input).hexdigest()[:16]

        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": answer
                    }
                ],
                "isError": False
            }
        })

    if request_id is None:
        return Response(status_code=202)

    return JSONResponse({
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": -32601,
            "message": "Method not found"
        }
    })
