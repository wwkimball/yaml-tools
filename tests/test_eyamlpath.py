import pytest

from subprocess import run
from types import SimpleNamespace

from ruamel.yaml import YAML

from yamlpath.eyaml import EYAMLPath
from yamlpath.wrappers import ConsolePrinter

requireseyaml = pytest.mark.skipif(
    not EYAMLPath.get_eyaml_executable("eyaml")
    , reason="The 'eyaml' command must be installed and accessible on the PATH"
        + " to test and use EYAML features.  Try:  'gem install hiera-eyaml'"
        + " after intalling ruby and rubygems."
)

@pytest.fixture
def eyamlpath():
    """Returns an EYAMLPath with a quiet logger."""
    args = SimpleNamespace(verbose=False, quiet=True, debug=False)
    logger = ConsolePrinter(args)
    return EYAMLPath(logger)

@requireseyaml
@pytest.fixture
def eyamldata():
    data = """---
aliases:
  - &secretIdentity >
    ENC[PKCS7,MIIBmQYJKoZIhvcNAQcDoIIBijCCAYYCAQAxggEhMIIBHQIBADAFMAACAQEw
    DQYJKoZIhvcNAQEBBQAEggEAUVX4h0PQVnxj5niYRvDPce/TisckEBqkOOcL
    ukGr+AFewRfLQ03zMUcr13jS5w7N6K9TIMPyc0QIvzL82a6jWpNAB7kFD+Ua
    lQcNwFIERYbo3SVn5+r8GTPzS82z59icEgFeL1ChNkL/vRYgys8IJrrJC/uS
    6QQ463hspwF2JyzUF7LM9Jc1EyGuJ1uektj/6jLxnYINrMazC61vb92++2Bk
    eMyFRZyCpJ/0ooHvhtF8ZxlLujPbgaUFCRpCxpXIYOGeTcrqgCZzkU3eUv2r
    PcCqlxHMOjN2SUXBY1pz8ApqErJ9/x0H9lZvD02XYclAMIWb8jouWJA0LaQ0
    Vvji7zBcBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBBVTmGQjl06z3JmnY65
    2STRgDB+D8ySgg5OezkWVRCWXyaei2yeLx4NhKUftXz1G4vbM2rCkFd5Unps
    u30g09oF92k=]
  - &secretPhrase >
    ENC[PKCS7,MIIBiQYJKoZIhvcNAQcDoIIBejCCAXYCAQAxggEhMIIBHQIBADAFMAACAQEw
    DQYJKoZIhvcNAQEBBQAEggEAXut3j+WbWxcl5Qh857pldvob8b+Av4VwtboA
    14g0slbMCemTtAW8fgpDzmrOGnvPvH5cjcY9FFXdvwa9U02NqosQKV0m7msD
    NirSWcQMGXaOBZqdedIohSHtUKz0QQ0GuEWxFGgXZjGbSwYSzdY6av5zEOFl
    IxGywYD0jLLFm+NkhKxj9wpPyq7qB1JsIqdAbuW33QwgYI8Hp6IBuQCZNFk/
    wnVn9ctInnPhLrvaDt6DN/ikT1d7F7VhteVQzFl3QoL6WW5pcg/vNVp7kvE9
    xJi6eop2BNOuv0Cvm5gJ6OsRX/a/JmA3jZmiweWk5Z3M6OEPpPwnqx1oz3cR
    ES762TBMBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBBlMyRzGtnxUiel+T+d
    uZFwgCA+DMcg3EllW8xXA7Kc4dhERJLb7VX2mtM9E2s4KrsIyw==]

anchored::secrets: &anchoredSecrets
  exposed_values:
    ident: This identity is in the wild.
    phrase: This phrase is in the wild.
  aliased_values:
    ident: *secretIdentity
    phrase: *secretPhrase

aliased::secrets:
  <<: *anchoredSecrets
  novel_values:
    ident: >
      ENC[PKCS7,MIIBmQYJKoZIhvcNAQcDoIIBijCCAYYCAQAxggEhMIIBHQIBADAFMAACAQEw
      DQYJKoZIhvcNAQEBBQAEggEAxum+Uyt3ETjkaQ9C5PqnpCUVCU6wrUYuVBk+
      PV7t7hayWGrG+dixzUUP9HKbIh6kbVYIwGCpEhMOmJQZ8TLiu/ye+KQzX/CE
      wz4uk7qvv/OvsFiMqmApxcvzNl2Qq7unCScXfngZKPjv4BxAFI1axzsUmxLx
      ChOUSkLMkuIJ5myAw43Sfan9Yx3lk96IoN97gN74ZzXTRGjl3n0zxrHy3obT
      M12f+MZqHuaTnuvksakk32nQ7jGX82QqxX3HChEkzUkKXG5ceS/cFzSTj9QG
      xbYrUXDNq/uviShfVk6tUey76VJAguLlw1ONqRkjonjAz7iR+YIu4RzvPvyJ
      Grz/ezBcBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBDcP+GwmSrNro9UALHI
      FoRFgDCwH91AbH9DOpDMj3HAOlxD2JzAkpy4X9SOZVn6Vht2do38Y1Z02Ccf
      pHj/ObATQ9M=]
    phrase: >
      ENC[PKCS7,MIIBygYJKoZIhvcNAQcDoIIBuzCCAbcCAQAxggEhMIIBHQIBADAFMAACAQEw
      DQYJKoZIhvcNAQEBBQAEggEAqaxguhCDS3afSGGsUvQ2bqDXQ71yIRa2sT3N
      1BH8d1fVDEo371jydJhRNg4bAwWjfvOIsuwhkEAtPSycvPNCimvAYz32dybA
      GsQxWo9KuQbmakQ+EDrkxtmS1yxQiUbWk7xw7XercPU8jKSqd3FfpRgKQAKV
      lQeFsCb8Cx/uWg2rS00SZ78LciYeFMwEhx2GYpjmOjdGkMVUKtJhPA24QAeF
      9QSpOmzpIdUho1hxBg9IP5K6HwgNBoYUMhL4xd8hhpRZUn0VSuERvKZAlRyh
      syT4tpPx6MWZw1UXWhPkZg66Fyq+MGJk5Q1zval6Kypqq83SisqsN2z4h1Zx
      WcXJMzCBjAYJKoZIhvcNAQcBMB0GCWCGSAFlAwQBKgQQZRyFQ+GeBvF2A9Yy
      QjUr5oBgwxfr7sa3oJfZNssJy4JlmUhfGVGN5GvxSGHM4zB+2c4lLx9Hk8MZ
      BBdpMsMcD8QqbTFpgOhKTh/pkT9DKP6CUcvSm7oxD7E8RtEyeIP3vH1UlulK
      A0INSZQsnGO+uGIX]
  string_values:
    ident: ENC[PKCS7,MIIBygYJKoZIhvcNAQcDoIIBuzCCAbcCAQAxggEhMIIBHQIBADAFMAACAQEwDQYJKoZIhvcNAQEBBQAEggEADFShQa5BcW0ctXJ6KGiadZYB2hPJrkO6tpOjz3qJzC6zuOrsL80NGOt9njDSEDQhpwvWHaREYJiv4WdBTdRuS2wVkxev/xDMCJrtrTSZ8aFZ2rFy7bkqBx5qiklOtgX2s9jUwzZ1y6YP7HbrBO2d3tO0Df79FvmcgwQOVRUk03BTczbA3xQc1Y50CBoS2d1VE8UxnSUUij3J/tOmugL9QkdSvBIyHwiKiy6brGgwaU1ddGPLMFdRXYN/gpyIbG595YhwTQfDWMp/2gBA7KZf941QJiIvxvq4LoYInNyBK+qTyaVmRRhDTxC4Cs0WfFlkPTkUdGu/GBc32+UDGwDOpTCBjAYJKoZIhvcNAQcBMB0GCWCGSAFlAwQBKgQQ/Ox/sWRra4DBDVh5a4QTD4Bg8v37JkY8S0fNbG/Dq5lRCz7/iQW7c1/f0JfRVIi7qTZfTRElrJo/+/o/SWq6bsj8eUA3UjooR07L0gerjOmd2p1kQQlZ1vEukbF/pnuptS07Gdrs4WlN/6KBIEJ//0Rc]
    phrase: ENC[PKCS7,MIIBqQYJKoZIhvcNAQcDoIIBmjCCAZYCAQAxggEhMIIBHQIBADAFMAACAQEwDQYJKoZIhvcNAQEBBQAEggEAR4DfxkRrYAHFQv97lXvaMyxy2iygBWgXWpKUBskCXbUAU0AZ56dsJS00ibVoRNpBoOkIwVN67G7/z084YA+Oqsg4Tw3NIIek14xChqL9m4ehtv1iMMutPM97wF2Yn2JRs63wKSN4l3nmTp/TFpko5rwj1rKap72mpDwrjJEWwRf4nzcdIzp6a7uWcBUVtG09Cu3VLUtoeAtKsIXVhMAZ2r/ozCSAbIQsFKiRPi2I8fL0ovhnmOXAmuB3eRStMDuGey0vCGYtFvWsmBoXkztIlfHB7/oXUJ5ABgu8D+9JmeXYQA4TjdL6gcQA+cNq9otvorTXnbNLgaRBCGFAqTvMhDBsBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBCw5QXmetCPTaxcpJWAefs+gEDo1hDNBXPFVhtvqqXUzicYZVxDADp2aUo/AdchuG15+8ic7K01aCdL4qkAtyx4HM16Hz0WVYIeiFyUgpCLY1EA]
"""
    yaml = YAML()
    return yaml.load(data)

@pytest.fixture(scope="module")
@requireseyaml
def eyamlkeys(tmp_path_factory):
    """Creates temporary keys for encryption/decryption tests."""
    private_key_file_name = "private_key.pkcs7.pem"
    public_key_file_name = "public_key.pkcs7.pem"
    old_key_path_name = "old-keys"
    new_key_path_name = "new-keys"
    old_private_key_file = tmp_path_factory.mktemp(old_key_path_name) / private_key_file_name
    old_public_key_file = tmp_path_factory.mktemp(old_key_path_name) / public_key_file_name
    new_private_key_file = tmp_path_factory.mktemp(new_key_path_name) / private_key_file_name
    new_public_key_file = tmp_path_factory.mktemp(new_key_path_name) / public_key_file_name

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

    run(
        "eyaml createkeys --pkcs7-private-key={} --pkcs7-public-key={}"
        .format(new_private_key_file, new_public_key_file).split()
    )

    return (
        old_private_key_file, old_public_key_file,
        new_private_key_file, new_public_key_file
    )

def test_find_eyaml_paths(eyamlpath, eyamldata):
    expected = [
        "aliases[&secretIdentity]",
        "aliases[&secretPhrase]",
        "anchored::secrets.aliased_values.ident",
        "anchored::secrets.aliased_values.phrase",
        "aliased::secrets.novel_values.ident",
        "aliased::secrets.novel_values.phrase",
        "aliased::secrets.string_values.ident",
        "aliased::secrets.string_values.phrase",
    ]
    actual = []
    for node in eyamlpath.find_eyaml_paths(eyamldata):
        actual.append(node)

    assert actual == expected

@requireseyaml
@pytest.mark.parametrize("search,compare", [
    ("aliases[&secretIdentity]", "This is not the identity you are looking for."),
    ("aliases[&secretPhrase]", "There is no secret phrase."),
])
def test_happy_get_eyaml_values(eyamlpath, eyamldata, eyamlkeys, search, compare):
    eyamlpath.privatekey = eyamlkeys[0]
    eyamlpath.publickey = eyamlkeys[1]
    for node in eyamlpath.get_eyaml_values(eyamldata, search, mustexist=True):
        eyamlpath.log.warning(node)
        assert node == compare

@requireseyaml
@pytest.mark.parametrize("search,compare,mustexist,output", [
    ("aliases[&secretIdentity]", "This is your new identity.", True, "string"),
    ("aliases[&brandNewEntry]", "This key doesn't already exist.", False, "block"),
])
def test_happy_set_eyaml_value(eyamlpath, eyamldata, eyamlkeys, search, compare, mustexist, output):
    # Assign the asymetric keys
    eyamlpath.privatekey = eyamlkeys[0]
    eyamlpath.publickey = eyamlkeys[1]

    # Set the test value
    eyamlpath.set_eyaml_value(eyamldata, search, compare, mustexist=mustexist, output=output)

    # Ensure the new value is encrypted
    for encnode in eyamlpath.get_nodes(eyamldata, search):
        assert EYAMLPath.is_eyaml_value(encnode)

    # Ensure the new value decrypts back to the original value
    for decnode in eyamlpath.get_eyaml_values(eyamldata, search, mustexist=True):
        assert decnode == compare

def test_none_eyaml_value():
    assert False == EYAMLPath.is_eyaml_value(None)

@requireseyaml
def test_impossible_eyaml_exe(eyamlpath, eyamlkeys):
    assert None == EYAMLPath.get_eyaml_executable("/no/such/file/anywhere")
    assert None == EYAMLPath.get_eyaml_executable("this-file-does-not-exist")
    assert None == EYAMLPath.get_eyaml_executable(eyamlkeys[0])
    assert None == EYAMLPath.get_eyaml_executable(None)

    eyamlpath.eyaml = None
    assert False == eyamlpath._can_run_eyaml()