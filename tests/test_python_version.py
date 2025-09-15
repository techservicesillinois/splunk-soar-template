import sys

SOAR_PYTHON_VERSION = (3, 13)


def test_python_version():
    """ Ensure python version in use matches SOAR python version. """
    assert sys.version_info.major == SOAR_PYTHON_VERSION[0]
    assert sys.version_info.minor == SOAR_PYTHON_VERSION[1]
