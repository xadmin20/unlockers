import base64


def crypt_str(string):
    return base64.urlsafe_b64encode((str(string)).encode("utf-8")).decode("utf-8")


def decrypt_str(string):
    return base64.urlsafe_b64decode(str(string)).decode('utf-8')


def create_session(request, name, value, crypt=False):
    if crypt:
        request.session[name] = crypt_str(str(value))
    else:
        request.session[name] = value


def get_session(request, name, crypt=False):
    result = 0
    if name in request.session:
        if crypt:
            result = decrypt_str(request.session[name])
        else:
            result = request.session[name]
    return result


def drop_session(request, name):
    if name in request.session:
        del request.session[name]
