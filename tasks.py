import os

from invoke import task, run

WHEELHOUSE_PATH = os.environ.get('WHEELHOUSE')


def monkey_patch():
    # Force an older cacert.pem from certifi v2015.4.28, prevents an ssl failure w/ identity.api.rackspacecloud.com.
    #
    # SubjectAltNameWarning: Certificate for identity.api.rackspacecloud.com has no `subjectAltName`, falling
    # back to check for a `commonName` for now. This feature is being removed by major browsers and deprecated by
    # RFC 2818. (See  https://github.com/shazow/urllib3/issues/497  for details.)
    # SubjectAltNameWarning
    import ssl
    import certifi

    _create_default_context = ssl.create_default_context

    def create_default_context(purpose=ssl.Purpose.SERVER_AUTH, *, cafile=None, capath=None, cadata=None):
        if cafile is None:
            cafile = certifi.where()
        return _create_default_context(purpose=purpose, cafile=cafile, capath=capath, cadata=cadata)
    ssl.create_default_context = create_default_context


@task
def wheelhouse(develop=False):
    req_file = 'dev-requirements.txt' if develop else 'requirements.txt'
    cmd = 'pip wheel --find-links={} -r {} --wheel-dir={}'.format(WHEELHOUSE_PATH, req_file, WHEELHOUSE_PATH)
    run(cmd, pty=True)


@task
def install(develop=False):
    run('python setup.py develop')
    req_file = 'dev-requirements.txt' if develop else 'requirements.txt'
    cmd = 'pip install --upgrade -r {}'.format(req_file)

    if WHEELHOUSE_PATH:
        cmd += ' --no-index --find-links={}'.format(WHEELHOUSE_PATH)
    run(cmd, pty=True)


@task
def flake():
    run('flake8 .', pty=True)


@task
def test(verbose=False):
    flake()
    cmd = 'py.test --cov-report term-missing --cov mfr tests'
    if verbose:
        cmd += ' -v'
    run(cmd, pty=True)


@task
def server():
    monkey_patch()
    from mfr.server.app import serve
    serve()
