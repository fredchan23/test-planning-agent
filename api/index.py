import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
                'body': f"<h1>App Import Error</h1><pre>{error_trace}</pre>".encode('utf-8'),
            })
