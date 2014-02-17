class Auth():

    def __init__(self, app):
        self._app = app

    def __call__(self, environ, start_response):
        if self._authenticated(environ.get('HTTP_AUTHORIZATION')):
            return self._app(environ, start_response)
        return self._login(environ, start_response)

    def _authenticated(self, header):
        from base64 import b64decode
        if not header:
            return False
        _, encoded = header.split(None, 1)
        decoded = b64decode(encoded).decode('UTF-8')
        username, password = decoded.split(':', 1)
        return username == password

    def _login(self, environ, start_response):
        start_response('401 Authentication Required',
            [('Content-Type', 'text/html'),
             ('WWW-Authenticate', 'Basic realm="Login"')])
        return [b'Login']


def app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [b'Hello, world!']


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('', 8000, Auth(app))
    print('Serving on port 8000...')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Goodbye!')