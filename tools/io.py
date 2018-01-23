


# DEP_APT( mosquitto mosquitto-clients )
from tools.daemon_class import simple_publish


def logging(source, msg, method='mqtt'):
    if method == 'mqtt':
        simple_publish('logging', '[ %s ] %s' % (source, msg))
    elif method == "stdout":
        print('[ %s ] %s' % (source, msg))


def out(source, msg, method='mqtt'):
    if method == 'mqtt':
        simple_publish(source, msg)


def test_internet(url='http://www.baidu.com'):
    from urllib.error import URLError
    from urllib.request import urlopen
    try:
        urlopen(url, timeout=1)
        return True
    except URLError as err:
        return False
