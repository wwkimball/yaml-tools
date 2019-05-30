import pytest

from subprocess import run, CalledProcessError

from ruamel.yaml import YAML

import yamlpath.patches
from yamlpath.enums import YAMLValueFormats
from yamlpath.eyaml.enums import EYAMLOutputFormats
from yamlpath.eyaml import EYAMLProcessor
from yamlpath.wrappers import ConsolePrinter
from yamlpath.eyaml.exceptions import EYAMLCommandException

from tests.conftest import requireseyaml, quiet_logger, old_eyaml_keys


@requireseyaml
@pytest.fixture
def eyamldata_f():
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
  array_of_array_idents:
    -
      - >
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

@pytest.fixture
def force_subprocess_run_cpe(monkeypatch):
    import yamlpath.eyaml.eyamlprocessor as break_module

    def fake_run(*args, **kwargs):
        raise CalledProcessError(42, "bad eyaml")

    monkeypatch.setattr(break_module, "run", fake_run)

@pytest.fixture
def force_no_access(monkeypatch):
    import yamlpath.eyaml.eyamlprocessor as break_module

    def fake_access(*args, **kwargs):
        return False

    monkeypatch.setattr(break_module, "access", fake_access)

class Test_eyaml_EYAMLProcessor():
    def test_find_eyaml_paths(self, quiet_logger, eyamldata_f):
        processor = EYAMLProcessor(quiet_logger, eyamldata_f)
        expected = [
            "aliases[&secretIdentity]",
            "aliases[&secretPhrase]",
            "anchored::secrets.aliased_values.ident",
            "anchored::secrets.aliased_values.phrase",
            "anchored::secrets.array_of_array_idents[0][0]",
            "aliased::secrets.novel_values.ident",
            "aliased::secrets.novel_values.phrase",
            "aliased::secrets.string_values.ident",
            "aliased::secrets.string_values.phrase",
        ]
        actual = []
        for path in processor.find_eyaml_paths():
            actual.append(str(path))

        assert actual == expected

    @requireseyaml
    @pytest.mark.parametrize("yaml_path,compare", [
        ("aliases[&secretIdentity]", "This is not the identity you are looking for."),
        ("aliases[&secretPhrase]", "There is no secret phrase."),
    ])
    def test_happy_get_eyaml_values(self, quiet_logger, eyamldata_f, old_eyaml_keys, yaml_path, compare):
        processor = EYAMLProcessor(quiet_logger, eyamldata_f, privatekey=old_eyaml_keys[0], publickey=old_eyaml_keys[1])
        for node in processor.get_eyaml_values(yaml_path, True):
            assert node == compare

    @requireseyaml
    @pytest.mark.parametrize("yaml_path,compare,mustexist,output_format", [
        ("aliases[&secretIdentity]", "This is your new identity.", True, EYAMLOutputFormats.STRING),
        ("aliases[&brandNewEntry]", "This key doesn't already exist.", False, EYAMLOutputFormats.BLOCK),
    ])
    def test_happy_set_eyaml_value(self, quiet_logger, eyamldata_f, old_eyaml_keys, yaml_path, compare, mustexist, output_format):
        processor = EYAMLProcessor(quiet_logger, eyamldata_f, privatekey=old_eyaml_keys[0], publickey=old_eyaml_keys[1])

        # Set the test value
        processor.set_eyaml_value(yaml_path, compare, output_format, mustexist)

        # Ensure the new value is encrypted
        encvalue = None
        for encnode in processor.get_nodes(yaml_path):
            encvalue = encnode
            break

        assert EYAMLProcessor.is_eyaml_value(encvalue)

    @requireseyaml
    @pytest.mark.parametrize("yaml_path,newval,eoformat,yvformat", [
        ("/aliased::secrets/novel_values/ident", "New, novel, encrypted identity in BLOCK format", EYAMLOutputFormats.BLOCK, YAMLValueFormats.FOLDED),
        ("/aliased::secrets/string_values/ident", "New, novel, encrypted identity in STRING format", EYAMLOutputFormats.STRING, YAMLValueFormats.BARE),
    ])
    def test_preserve_old_blockiness(self, quiet_logger, eyamldata_f, old_eyaml_keys, yaml_path, newval, eoformat, yvformat):
        processor = EYAMLProcessor(quiet_logger, eyamldata_f, privatekey=old_eyaml_keys[0], publickey=old_eyaml_keys[1])
        processor.set_eyaml_value(yaml_path, newval, output=eoformat)

        encvalue = None
        encformat = YAMLValueFormats.DEFAULT
        for encnode in processor.get_nodes(yaml_path):
            encvalue = encnode
            encformat = YAMLValueFormats.from_node(encvalue)
            break

        assert EYAMLProcessor.is_eyaml_value(encvalue) and yvformat == encformat

    def test_none_eyaml_value(self):
        assert False == EYAMLProcessor.is_eyaml_value(None)

    @pytest.mark.parametrize("exe", [
        ("/no/such/file/anywhere"),
        ("this-file-does-not-exist"),
        (None),
    ])
    def test_impossible_eyaml_exe(self, exe):
        assert None == EYAMLProcessor.get_eyaml_executable(exe)

    def test_not_can_run_eyaml(self, quiet_logger):
        processor = EYAMLProcessor(quiet_logger, None)
        processor.eyaml = None
        assert False == processor._can_run_eyaml()

    @requireseyaml
    def test_bad_encryption_keys(self, quiet_logger):
        processor = EYAMLProcessor(quiet_logger, None)
        processor.privatekey = "/no/such/file"
        processor.publickey = "/no/such/file"

        with pytest.raises(EYAMLCommandException):
            processor.encrypt_eyaml("test")

    def test_no_encrypt_without_eyaml(self, quiet_logger):
        processor = EYAMLProcessor(quiet_logger, None)
        processor.eyaml = None
        with pytest.raises(EYAMLCommandException):
            processor.encrypt_eyaml("test")

    def test_no_decrypt_without_eyaml(self, quiet_logger):
        processor = EYAMLProcessor(quiet_logger, None)
        processor.eyaml = None
        with pytest.raises(EYAMLCommandException):
            processor.decrypt_eyaml("ENC[...]")

    def test_ignore_already_encrypted_cryps(self, quiet_logger):
        processor = EYAMLProcessor(quiet_logger, None)
        testval = "ENC[...]"
        assert testval == processor.encrypt_eyaml(testval)

    def test_ignore_already_decrypted_cryps(self, quiet_logger):
        processor = EYAMLProcessor(quiet_logger, None)
        testval = "some value"
        assert testval == processor.decrypt_eyaml(testval)

    @requireseyaml
    def test_impossible_decryption(self, quiet_logger, old_eyaml_keys):
        processor = EYAMLProcessor(quiet_logger, None)
        testval = "ENC[...]"
        with pytest.raises(EYAMLCommandException):
            processor.decrypt_eyaml(testval)

    def test_encrypt_calledprocesserror(self, quiet_logger, force_subprocess_run_cpe):
        processor = EYAMLProcessor(quiet_logger, None)
        with pytest.raises(EYAMLCommandException):
            processor.encrypt_eyaml("any value")

    def test_decrypt_calledprocesserror(self, quiet_logger, force_subprocess_run_cpe):
        processor = EYAMLProcessor(quiet_logger, None)
        with pytest.raises(EYAMLCommandException):
            processor.decrypt_eyaml("ENC[...]")

    @requireseyaml
    def test_non_executable(self, old_eyaml_keys, force_no_access):
        assert EYAMLProcessor.get_eyaml_executable(str(old_eyaml_keys[0])) is None
