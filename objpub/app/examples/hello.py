def index(req, res):
    return 'Hello, {}!'.format(req.fields.get('name', 'World'))

def json(req, res):
    from json import dumps
    res.headers['Content-Type'] = 'application/json'
    return dumps({ 'message': 'Hello, {}!'.format(req.fields.get('name', 'World')) })