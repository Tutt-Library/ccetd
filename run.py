from etd import app
from werkzeug.wsgi import DispatcherMiddleware
from werkzeug.serving import run_simple

def simple(env, resp):
    resp(b'200 OK', [('Content-Type', b'text/plain')])
    return [b'CCETD World']

parent_app = DispatcherMiddleware(
    simple, 
    {"/etd": app})

if app.config.get("DEBUG") is True:
    parent_app.debug = True

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8084, debug=True)
#     run_simple('0.0.0.0', 8095, parent_app, use_reloader=True, use_debugger=True)
