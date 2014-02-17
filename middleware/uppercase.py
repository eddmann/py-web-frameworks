class Uppercase():

    def __init__(self, app):
        self._app = app

    def __call__(self, environ, start_response):
        response = self._app(environ, start_response)
        return map(lambda s: s.decode('UTF-8').upper().encode('UTF-8'), response)


def app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [b'Hello, world!']


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('', 8000, Uppercase(app))
    print('Serving on port 8000...')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Goodbye!')