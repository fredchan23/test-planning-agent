import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import litellm
    litellm_status = "LiteLLM imported successfully"
except Exception as e:
    litellm_status = f"LiteLLM Import Failed:\n{traceback.format_exc()}"

try:
    from test_planner_agent.app import app as _app
except Exception as e:
    _app = None
    error_trace = traceback.format_exc()

async def app(scope, receive, send):
    if _app:
        await _app(scope, receive, send)
    else:
        if scope['type'] == 'http':
            await send({
                'type': 'http.response.start',
                'status': 500,
                'headers': [[b'content-type', b'text/html']],
            })
            await send({
                'type': 'http.response.body',
                'body': f"<h1>App Import Error</h1><pre>{error_trace}</pre><h2>LiteLLM Status</h2><pre>{litellm_status}</pre>".encode('utf-8'),
            })
