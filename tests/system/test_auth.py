"""System tests for fetching Google BigQuery credentials."""

import os

try:
    import mock
except ImportError:  # pragma: NO COVER
    from unittest import mock
import pytest

from pandas_gbq import auth


@pytest.fixture
def project_id():
    return (os.environ.get('GBQ_PROJECT_ID')
            or os.environ.get('GOOGLE_CLOUD_PROJECT'))  # noqa


@pytest.fixture
def private_key_path():
    path = None
    if 'TRAVIS_BUILD_DIR' in os.environ:
        path = os.path.join(
            os.environ['TRAVIS_BUILD_DIR'], 'ci',
            'travis_gbq.json')
    elif 'GBQ_GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
        path = os.environ['GBQ_GOOGLE_APPLICATION_CREDENTIALS']
    elif 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
        path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']

    if path is None:
        pytest.skip("Cannot run integration tests without a "
                    "private key json file path")
    elif not os.path.isfile(path):
        pytest.skip("Cannot run integration tests when there is"
                    "no file at the private key json file path")
    return path


@pytest.fixture
def private_key_contents(private_key_path):
    if private_key_path is None:
        return None

    with open(private_key_path) as f:
        return f.read()


def _check_if_can_get_correct_default_credentials():
    # Checks if "Application Default Credentials" can be fetched
    # from the environment the tests are running in.
    # See https://github.com/pandas-dev/pandas/issues/13577

    import google.auth
    from google.auth.exceptions import DefaultCredentialsError
    import pandas_gbq.auth
    import pandas_gbq.gbq

    try:
        credentials, project = google.auth.default(
            scopes=pandas_gbq.auth.SCOPES)
    except (DefaultCredentialsError, IOError):
        return False

    return auth._try_credentials(project, credentials) is not None


def test_should_be_able_to_get_valid_credentials(project_id, private_key_path):
    credentials, _ = auth.get_credentials(
        project_id=project_id, private_key=private_key_path)
    assert credentials.valid


def test_get_service_account_credentials_private_key_path(private_key_path):
    from google.auth.credentials import Credentials
    credentials, project_id = auth.get_service_account_credentials(
        private_key_path)
    assert isinstance(credentials, Credentials)
    assert auth._try_credentials(project_id, credentials) is not None


def test_get_service_account_credentials_private_key_contents(
        private_key_contents):
    from google.auth.credentials import Credentials
    credentials, project_id = auth.get_service_account_credentials(
        private_key_contents)
    assert isinstance(credentials, Credentials)
    assert auth._try_credentials(project_id, credentials) is not None


def test_get_application_default_credentials_does_not_throw_error():
    if _check_if_can_get_correct_default_credentials():
        # Can get real credentials, so mock it out to fail.
        from google.auth.exceptions import DefaultCredentialsError
        with mock.patch('google.auth.default',
                        side_effect=DefaultCredentialsError()):
            credentials, _ = auth.get_application_default_credentials()
    else:
        credentials, _ = auth.get_application_default_credentials()
    assert credentials is None


def test_get_application_default_credentials_returns_credentials():
    if not _check_if_can_get_correct_default_credentials():
        pytest.skip("Cannot get default_credentials "
                    "from the environment!")
    from google.auth.credentials import Credentials
    credentials, default_project = auth.get_application_default_credentials()

    assert isinstance(credentials, Credentials)
    assert default_project is not None


@pytest.mark.local_auth
def test_get_user_account_credentials_bad_file_returns_credentials():
    from google.auth.credentials import Credentials
    with mock.patch('__main__.open', side_effect=IOError()):
        credentials = auth.get_user_account_credentials()
    assert isinstance(credentials, Credentials)


@pytest.mark.local_auth
def test_get_user_account_credentials_returns_credentials(project_id):
    from google.auth.credentials import Credentials
    credentials = auth.get_user_account_credentials(
        project_id=project_id,
        auth_local_webserver=True)
    assert isinstance(credentials, Credentials)


@pytest.mark.local_auth
def test_get_user_account_credentials_reauth_returns_credentials(project_id):
    from google.auth.credentials import Credentials
    credentials = auth.get_user_account_credentials(
        project_id=project_id,
        auth_local_webserver=True,
        reauth=True)
    assert isinstance(credentials, Credentials)
