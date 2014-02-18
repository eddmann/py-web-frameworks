from cgi import parse_qs
from PIL import Image
from webob import Request
import os, io, mimetypes


class Foto():

    def __init__(self, app, url, aliases):
        self._app = app
        self._url = url
        self._aliases = { k: os.path.realpath(v) for k, v in aliases.items() }

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '').strip('/')
        if path != self._url:
            return self._app(environ, start_response)

        req = Request(environ)

        try:
            src = req.GET.getone('s')
            img = self._parse_src(src)
        except (KeyError, FileNotFoundError) as ex:
            print(ex)
            return self._not_found(start_response)

        try:
            width = int(req.GET.getone('w'))
        except KeyError:
            width = 0

        try:
            height = int(req.GET.getone('h'))
        except KeyError:
            height = 0

        if width == 0:
            width = height

        if height == 0:
            height = width

        if width == 0:
            img, mime = self._thumbnail(img, (100, 100))
        else:
            img, mime = self._resize(img, (width, height))

        start_response('200 OK', [('Content-Type', mime)])
        return [img.getvalue()]

    def _not_found(self, start_response):
        start_response('404 Not Found', [('Content-Type', 'text/html')])
        return []

    def _parse_src(self, src):
        alias, path = src.split(':', 1)
        full_path = os.path.join(self._aliases[alias], path.strip('/'))
        print('Attempting to open:', full_path)
        return Image.open(full_path)

    def _resize(self, img, size):
        fmt = img.format
        out = io.BytesIO()
        img.thumbnail(size, Image.ANTIALIAS)
        img.save(out, fmt, quality=100)
        return out, mimetypes.types_map['.' + fmt.lower()]

    def _thumbnail(self, img, size, crop='middle'):
        fmt = img.format

        img_ratio = img.size[0] / float(img.size[1])
        ratio = size[0] / float(size[1])
        if ratio > img_ratio:
            img = img.resize((size[0], round(size[0] * img.size[1] / img.size[0])),
                             Image.ANTIALIAS)
            if crop == 'top':
                box = (0, 0, img.size[0], size[1])
            elif crop == 'middle':
                box = (0, round((img.size[1] - size[1]) / 2), img.size[0],
                       round((img.size[1] + size[1]) / 2))
            elif crop == 'bottom':
                box = (0, img.size[1] - size[1], img.size[0], img.size[1])
            else:
                raise ValueError('Invalid cropping type.')
            img = img.crop(box)
        elif ratio < img_ratio:
            img = img.resize((round(size[1] * img.size[0] / img.size[1]), size[1]),
                             Image.ANTIALIAS)
            if crop == 'top':
                box = (0, 0, size[0], img.size[1])
            elif crop == 'middle':
                box = (round((img.size[0] - size[0]) / 2), 0,
                       round((img.size[0] + size[0]) / 2), img.size[1])
            elif crop == 'bottom':
                box = (img.size[0] - size[0], 0, img.size[0], img.size[1])
            else:
                raise ValueError('Invalid cropping type.')
            img = img.crop(box)
        else:
            img = img.resize((size[0], size[1]), Image.ANTIALIAS)

        out = io.BytesIO()
        img.save(out, fmt, quality=100)
        return out, mimetypes.types_map['.' + fmt.lower()]


def app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
    return [b'Hello, world!']


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('', 8000, Foto(app, url='foto', aliases={'photos':'./middleware/photos'}))
    print('Serving on port 8000...')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Goodbye!')