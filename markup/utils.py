import base64


def crypt_str(string):
    return base64.urlsafe_b64encode((str(string)).encode("utf-8")).decode("utf-8")


def decrypt_str(string):
    return base64.urlsafe_b64decode(str(string)).decode('utf-8')


def create_session(request, name, value, crypt=False):
    if crypt:
        encoded_value = crypt_str(str(value))
        request.session[name] = encoded_value
    else:
        request.session[name] = value


def get_session(request, name, crypt=False):
    if name not in request.session:
        print(f"Session key {name} not found.")
        return None  # возвращаем None вместо 0

    if crypt:
        try:
            decrypted_value = decrypt_str(request.session[name])
            print(f"Got session (decrypted): {name} -> {decrypted_value} (encoded: {request.session[name]})")
            return decrypted_value
        except Exception as e:
            print(f"Error decrypting session value for key {name}. Error: {e}")
            return None  # возвращаем None в случае ошибки
    else:
        print(f"Got session: {name} -> {request.session[name]}")
        return request.session[name]


def drop_session(request, name):
    if name in request.session:
        del request.session[name]
