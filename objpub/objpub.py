"""Object-Publisher Web Framework

Inspired by: http://pythonpaste.org/do-it-yourself-framework.html#object-publishing

$ python3 -B objpub.py
"""

from cgi import parse_qs
import threading


def lazyproperty(fn):
    """http://stackoverflow.com/questions/3012421/python-lazy-property-decorator"""
    attr_name = '_lazy_' + fn.__name__
    @property
    def _lazyproperty(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)
    return _lazyproperty


class Request:
    """Handles GET and POST request fields."""

    def __init__(self, environ):
        self.environ = environ

    @lazyproperty
    def get(self):
        orig = parse_qs(self.environ.get('QUERY_STRING', ''))
        return { k: v if len(v) > 1 else v[0] for k, v in orig.items() }

    @lazyproperty
    def post(self):
        try:
            body_size = int(self.environ.get('CONTENT_LENGTH', 0))
        except ValueError:
            body_size = 0
        request_body = self.environ['wsgi.input'].read(body_size)
        orig = parse_qs(request_body)
        return { k: v if len(v) > 1 else v[0] for k, v in orig.items() }

    @lazyproperty
    def fields(self):
        return dict(self.get, **self.post)


class Response:
    """Handles the response headers."""

    def __init__(self):
        self.headers = { 'Content-Type': 'text/html' }

    def get_headers(self):
        return [ (k, v) for k, v in self.headers.items() ]


web = threading.local()

class App:
    """Where the magic happens."""

    def __init__(self, ns, root):
        self.ns = ns.split('.')
        self.root = root.split('.')

    def __call__(self, environ, start_response):
        web.request = Request(environ)
        web.response = Response()
        try:
            action = self.get_action(environ.get('PATH_INFO'))
            response_body = action(req=web.request, res=web.response)
            start_response('200 OK', web.response.get_headers())
            return [ response_body if isinstance(response_body, bytes) else response_body.encode('UTF-8') ]
        except ImportError:
            start_response('404 Not Found', web.response.get_headers())
            return [b'Not Found']

    def _get_action(self, path, attr):
        ns = '.'.join(path)
        parent = '.'.join(path[:-1])
        module = __import__(ns, fromlist=[parent])
        try:
            fn = getattr(module, attr)
            if fn is None or not callable(fn):
                raise ImportError
        except AttributeError:
            raise ImportError
        return fn

    def get_action(self, request):
        request = request.strip('/').split('/')

        # root function request
        if (len(request) == 1):
            try:
                return self._get_action(self.ns + self.root, request[0] or 'index')
            except ImportError:
                pass

        path = self.ns + request

        # module request index page
        try:
            return self._get_action(path, 'index')
        except ImportError:
            pass

        # module function request
        return self._get_action(path[:-1], path[-1])


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    app = App('app', 'root')
    httpd = make_server('', 8000, app)
    print('Serving on port 8000...')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Goodbye!')