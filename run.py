from etd import app
from werkzeug.wsgi import DispatcherMiddleware

def simple(env, resp):
    resp(b'200 OK', [('Content-Type', b'text/plain')])
    return [b'CCETD World']

parent_app = DispatcherMiddleware(
    simple, 
    {"/etd": app})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8095, debug=True)
