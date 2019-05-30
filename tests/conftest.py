"""Define reusable pytest fixtures."""
import tempfile
from types import SimpleNamespace

import pytest

from yamlpath.wrappers import ConsolePrinter
from yamlpath.eyaml import EYAMLProcessor

# Implied constants
EYAML_PRIVATE_KEY_FILENAME = "private_key.pkcs7.pem"
EYAML_PUBLIC_KEY_FILENAME = "public_key.pkcs7.pem"

# pylint: disable=locally-disabled,invalid-name
requireseyaml = pytest.mark.skipif(
    EYAMLProcessor.get_eyaml_executable("eyaml") is None
    , reason="The 'eyaml' command must be installed and accessible on the PATH"
        + " to test and use EYAML features.  Try:  'gem install hiera-eyaml'"
        + " after intalling ruby and rubygems."
)

@pytest.fixture
def quiet_logger():
    """Returns a quiet ConsolePrinter."""
    args = SimpleNamespace(verbose=False, quiet=True, debug=False)
    return ConsolePrinter(args)

@pytest.fixture(scope="session")
def old_eyaml_keys(tmp_path_factory):
    """Creates temporary keys for encryption/decryption tests."""
    old_key_path_name = "old-keys"
    old_key_dir = tmp_path_factory.mktemp(old_key_path_name)
    old_private_key_file = old_key_dir / EYAML_PRIVATE_KEY_FILENAME
    old_public_key_file = old_key_dir / EYAML_PUBLIC_KEY_FILENAME

    old_private_key = r"""-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1BuytnsdHdt6NkNfLoGJIlf9hrWux8raPP3W57cONh2MrQ6d
aoAX+L+igTSjvSTI6oxsO0dqdYXZO1+rOK3gI9OnZQhkCjq9IRoWx7AIvM7skaD0
Lne9YsvA7mGY/z9lm3IALI6OBVV5k6xnBR2PVi6A7FnDm0CRLit2Bn9eHLN3k4oL
S/ynxgXBmWWgnKtJNJwGmeD5PwzJfXCcJ3kPItiktFizJZoPmAlBP7LIzamlfSXV
VoniRs45aGrTGpmZSdvossL41KBCYJGjP+lIL/UpDJHBeiuqVQoDl4/UZqb5xF9S
C2p2Of21fmZmj4uUAT5FPtKMKCspmLWQeUEfiwIDAQABAoIBAEyXR9wu7p+mbiYE
A+22Jr+5CDpJhrhsXovhmWWIq2ANIYwoF92qLX3MLTD8whd9nfNcC4UIT7/qOjv/
WsOXvbUSK4MHGaC7/ylh01H+Fdmf2rrnZOUWpdN0AdHSej3JNbaA3uE4BL6WU9Vo
TrcBKo4TMsilzUVVdlc2qGLGQUSZPLnIJWMLQIdCe2kZ9YvUlGloD4uGT3RH6+vH
TOtXqDgLGS/79K0rnflnBsUBkXpukxzOcTRHxR0s7SJ2XCB0JfdLWfR6X1nzM4mh
rn/m2nzEOG9ICe5hoHqAEZ/ezKd/jwxMg1YMZnGAzDMw7/UPWo87wgVdxxOHOsHG
v/pK+okCgYEA/SToT82qtvWIiUTbkdDislGhTet2eEu2Bi9wCxAUQn045Y812r9d
TvJyfKJyvvpxzejaecJb8oOXyypMDay7aPOVBI1E2OqfImxF8pJ0QqejAUCinXrj
KnV72L/hjTavivWq1vHZYXSxufAMG0C7UeztwkOfk85N3wuuYYWYrc0CgYEA1oBG
2fQ0PXDyionE3c4bpRGZMJxD+3RFRMCJiE+xheRR22ObSDLUH123ZGmU0m2FTS9O
M+GJbZgdV1Oe0EJ5rWfzFYUmVJIreH+oQWaY/HMkoe705LAMcPyd0bSjRVWWiz+l
anIGjj5HaPSI7XFqdQu7j3ww67k4BBAca8++arcCgYA/cIhnt3sY7t+QxxjfqiGl
3p82D9RYwWCUnD7QBu+M2iTwIru0XlDcABaA9ZUcF1d96uUVroesdx4LZEY7BxbQ
bnrh8SVX1zSaQ9gjumA4dBp9rd0S6kET2u12nF/CK/pCMN7njySTL9N6bZYbHlXT
ajULgjbzq7gINb01420n4QKBgQCqu0epy9qY3QHwi2ALPDZ82NkZ/AeQaieIZcgS
m3wtmmIdQdcjTHHS1YFXh0JRi6MCoJiaavY8KUuRapmKIp8/CvJNOsIbpoy7SMDf
7Y3vwqZxzgVW0VnVxPzJIgKi+VDuXSaI52GYbrHgNGOYuyGFMGWF+8/kkHSppzk4
Bw8FWQKBgQCo/7cV19n3e7ZlZ/aGhIOtSCTopMBV8/9PIw+s+ZDiQ7vRSj9DwkAQ
+x97V0idgh16tnly0xKvGCGTQR7qDsDTjHmmF4LZUGjcq7pHsTi/umCM/toE+BCk
7ayr+G0DWr5FjhQ7uCt2Rz1NKcj6EkDcM1WZxkDLAvBXjlj+T+eqtQ==
-----END RSA PRIVATE KEY-----
"""
    old_public_key = r"""-----BEGIN CERTIFICATE-----
MIIC2TCCAcGgAwIBAgIBATANBgkqhkiG9w0BAQsFADAAMCAXDTE5MDUwNzE4MDAw
NVoYDzIwNjkwNDI0MTgwMDA1WjAAMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIB
CgKCAQEA1BuytnsdHdt6NkNfLoGJIlf9hrWux8raPP3W57cONh2MrQ6daoAX+L+i
gTSjvSTI6oxsO0dqdYXZO1+rOK3gI9OnZQhkCjq9IRoWx7AIvM7skaD0Lne9YsvA
7mGY/z9lm3IALI6OBVV5k6xnBR2PVi6A7FnDm0CRLit2Bn9eHLN3k4oLS/ynxgXB
mWWgnKtJNJwGmeD5PwzJfXCcJ3kPItiktFizJZoPmAlBP7LIzamlfSXVVoniRs45
aGrTGpmZSdvossL41KBCYJGjP+lIL/UpDJHBeiuqVQoDl4/UZqb5xF9SC2p2Of21
fmZmj4uUAT5FPtKMKCspmLWQeUEfiwIDAQABo1wwWjAPBgNVHRMBAf8EBTADAQH/
MB0GA1UdDgQWBBTUHb3HX8dBfYFL1J1sCv+uCum5AzAoBgNVHSMEITAfgBTUHb3H
X8dBfYFL1J1sCv+uCum5A6EEpAIwAIIBATANBgkqhkiG9w0BAQsFAAOCAQEAcw+0
dfHSLNAZD95G2pDnT2qShjmdLdbrDQhAXWhLeoWpXsKvC0iUyQaOF9ckl++tHM2g
ejm1vEOrZ+1uXK3qnMXPF99Wet686OhyoDt262Mt3wzGHNijAHEvQtjap8ZIwfOM
zFTvjmOlUScqF/Yg+htcGnJdQhWIrsD+exiY5Kz2IMtuW+yWLLP8bY5vPg6qfrp2
4VVJ3Md1gdSownd1Au5tqPXm6VfSgLiCm9iDPVsjDII9h8ydate1d2TBHPup+4tN
JZ5/muctimydC+S2oCn7ucsilxZD89N7rJjKXNfoUOGHjOEVQMa8RtZLzH2sUEaS
FktE6rH8a+8SwO+TGw==
-----END CERTIFICATE-----
"""

    with open(old_private_key_file, 'w') as key_file:
        key_file.write(old_private_key)

    with open(old_public_key_file, 'w') as key_file:
        key_file.write(old_public_key)

    return (old_private_key_file, old_public_key_file)

@requireseyaml
@pytest.fixture(scope="session")
def new_eyaml_keys(tmp_path_factory):
    """Creates temporary keys for encryption/decryption tests."""
    from subprocess import run

    new_key_path_name = "new-keys"
    new_key_dir = tmp_path_factory.mktemp(new_key_path_name)
    new_private_key_file = new_key_dir / EYAML_PRIVATE_KEY_FILENAME
    new_public_key_file = new_key_dir / EYAML_PUBLIC_KEY_FILENAME

    run(
        "{} createkeys --pkcs7-private-key={} --pkcs7-public-key={}"
        .format(
            EYAMLProcessor.get_eyaml_executable("eyaml"),
            new_private_key_file,
            new_public_key_file
        )
        .split()
    )

    return (new_private_key_file, new_public_key_file)

def create_temp_yaml_file(tmp_path_factory, content):
    """Creates a test YAML input file."""
    fhnd = tempfile.NamedTemporaryFile(mode='w',
                                       dir=tmp_path_factory.getbasetemp(),
                                       suffix='.yaml',
                                       delete=False)
    fhnd.write(content)
    return fhnd.name

@pytest.fixture(scope="session")
def imparsible_yaml_file(tmp_path_factory):
    """
    Creates a YAML file that causes a ParserError when read by ruamel.yaml.
    """
    content = '''{"json": "is YAML", "but_bad_json": "isn't anything!"'''
    return create_temp_yaml_file(tmp_path_factory, content)

@pytest.fixture(scope="session")
def badsyntax_yaml_file(tmp_path_factory):
    """
    Creates a YAML file that causes a ScannerError when read by ruamel.yaml.
    """
    content = """---
    # This YAML content contains a critical syntax error
    & bad_anchor: is bad
    """
    return create_temp_yaml_file(tmp_path_factory, content)

@pytest.fixture(scope="session")
def badcmp_yaml_file(tmp_path_factory):
    """
    Creates a YAML file that causes a ComposerError when read by ruamel.yaml.
    """
    content = """---
    # This YAML file is improperly composed
    this is a parsing error: *no such capability
    """
    return create_temp_yaml_file(tmp_path_factory, content)
