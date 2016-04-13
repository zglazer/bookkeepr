from threading import Thread

def async(f):
    def wrapper(*args, **kwargs):
        t = Thread(target = f, args = args, kwargs = kwargs)
        t.start()
    return wrapper
