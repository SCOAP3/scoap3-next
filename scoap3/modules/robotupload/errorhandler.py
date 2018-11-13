class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, description, status_code=None, payload=None):
        Exception.__init__(self)
        self.description = description
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict()
        rv['error'] = self.status_code
        rv['description'] = self.description
        if self.payload:
            rv['message'] = self.payload
        return rv
