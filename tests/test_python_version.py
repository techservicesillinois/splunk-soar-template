import sys


def test_python_version():
    """ Ensure python version in use matches SOAR python version. """
    assert sys.version_info.major == 3
    assert sys.version_info.minor == 8
