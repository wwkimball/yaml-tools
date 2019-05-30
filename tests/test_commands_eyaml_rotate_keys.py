import pytest

from tests.conftest import (
    create_temp_yaml_file,
    requireseyaml,
    old_eyaml_keys,
    new_eyaml_keys,
)

class Test_eyaml_rotate_keys():
    """Tests for the eyaml-rotate-keys command-line interface."""
    command = "eyaml-rotate-keys"

    def test_no_options(self, script_runner):
        result = script_runner.run(self.command)
        assert not result.success, result.stderr
        assert "usage: {}".format(self.command) in result.stderr

    def test_duplicate_keys(self, script_runner):
        bunk_key = "/does/not/exist/on-most/systems"
        result = script_runner.run(
            self.command,
            "--newprivatekey={}".format(bunk_key),
            "--newpublickey={}".format(bunk_key),
            "--oldprivatekey={}".format(bunk_key),
            "--oldpublickey={}".format(bunk_key),
            bunk_key
        )
        assert not result.success, result.stderr
        assert "The new and old EYAML keys must be different." in result.stderr

    def test_bad_keys(self, script_runner):
        bunk_file = "/does/not/exist/on-most/systems"
        bunk_old_key = "/does/not/exist/on-most/systems/old"
        bunk_new_key = "/does/not/exist/on-most/systems/new"
        result = script_runner.run(
            self.command,
            "--newprivatekey={}".format(bunk_new_key),
            "--newpublickey={}".format(bunk_new_key),
            "--oldprivatekey={}".format(bunk_old_key),
            "--oldpublickey={}".format(bunk_old_key),
            bunk_file
        )
        assert not result.success, result.stderr
        assert "EYAML key is not a readable file:" in result.stderr

    @requireseyaml
    def test_no_yaml_files(self, script_runner, old_eyaml_keys, new_eyaml_keys):
        bunk_file = "/does/not/exist/on-most/systems"
        result = script_runner.run(
            self.command,
            "--newprivatekey={}".format(new_eyaml_keys[0]),
            "--newpublickey={}".format(new_eyaml_keys[1]),
            "--oldprivatekey={}".format(old_eyaml_keys[0]),
            "--oldpublickey={}".format(old_eyaml_keys[1]),
            bunk_file
        )
        assert not result.success, result.stderr
        assert "Not a file:" in result.stderr

    @requireseyaml
    def test_good_multi_replacements(self, script_runner, tmp_path_factory, old_eyaml_keys, new_eyaml_keys):
        simple_content = """---
        encrypted_string: ENC[PKCS7,MIIBiQYJKoZIhvcNAQcDoIIBejCCAXYCAQAxggEhMIIBHQIBADAFMAACAQEwDQYJKoZIhvcNAQEBBQAEggEAHA4rPcTzvgzPLtnGz3yoyX/kVlQ5TnPXcScXK2bwjguGZLkuzv/JVPAsOm4t6GlnROpy4zb/lUMHRJDChJhPLrSj919B8//huoMgw0EU5XTcaN6jeDDjL+vhjswjvLFOux66UwvMo8sRci/e2tlFiam8VgxzV0hpF2qRrL/l84V04gL45kq4PCYDWrJNynOwYVbSIF+qc5HaF25H8kHq1lD3RB6Ob/J942Q7k5Qt7W9mNm9cKZmxwgtUgIZWXW6mcPJ2dXDB/RuPJJSrLsb1VU/DkhdgxaNzvLCA+MViyoFUkCfHFNZbaHKNkoYXBy7dLmoh/E5tKv99FeG/7CzL3DBMBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBCVU5Mjt8+4dLkoqB9YArfkgCDkdIhXR9T1M4YYa1qTE6by61VPU3g1aMExRmo4tNZ8FQ==]
        encrypted_block: >
          ENC[PKCS7,MIIBeQYJKoZIhvcNAQcDoIIBajCCAWYCAQAxggEhMIIBHQIBADAFMAACAQEw
          DQYJKoZIhvcNAQEBBQAEggEAnxQVqyIgRTb/+VP4Q+DLJcnlS8YPouXEW8+z
          it9uwUA02CEPxCEU944GcHpgTY3EEtkm+2Z/jgXI119VMML+OOQ1NkwUiAw/
          wq0vwz2D16X31XzhedQN5FZbfZ1C+2tWSQfCjE0bu7IeHfyR+k2ssD11kNZh
          JDEr2bM2dwOdT0y7VGcQ06vI9gw6UXcwYAgS6FoLm7WmFftjcYiNB+0EJSW0
          VcTn2gveaw9iOQcum/Grby+9Ybs28fWd8BoU+ZWDpoIMEceujNa9okIXNPJO
          jcvv1sgauwJ3RX6WFQIy/beS2RT5EOLhWIZCAQCcgJWgovu3maB7dEUZ0NLG
          OYUR7zA8BgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBAbO16EzQ5/cdcvgB0g
          tpKIgBAEgTLT5n9Jtc9venK0CKso]
        """
        anchored_content = """---
        aliases:
          - &blockStyle >
            ENC[PKCS7,MIIBiQYJKoZIhvcNAQcDoIIBejCCAXYCAQAxggEhMIIBHQIBADAFMAACAQEw
            DQYJKoZIhvcNAQEBBQAEggEArvk6OYa1gACTdrWq2SpCrtGRlc61la5AGU7L
            aLTyKfqD9vqx71RDjobfOF96No07kLsEpoAJ+LKKHNjdG6kjvpGPmttj9Dkm
            XVoU6A+YCmm4iYFKD/NkoSOEyAkoDOXSqdjrgt0f37GefEsXt6cqAavDpUJm
            pmc0KI4TCG5zpfCxqttMs+stOY3Y+0WokkulQujZ7K3SdWUSHIysgMrWiect
            Wdg5unxN1A/aeyvhgvYSNPjU9KBco7SDnigSs9InW/QghJFrZRrDhTp1oTUc
            qK5lKvaseHkVGi91vPWeLQxZt1loJB5zL6j5BxMbvRfJK+wc3ax2u4x8WTAB
            EurCwzBMBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBAwcy7jvcOGcMfLEtug
            LEXbgCBkocdckuDe14mVGmUmM++xN34OEVRCeGVWWUnWq1DJ4Q==]
          - &stringStyle ENC[PKCS7,MIIBiQYJKoZIhvcNAQcDoIIBejCCAXYCAQAxggEhMIIBHQIBADAFMAACAQEwDQYJKoZIhvcNAQEBBQAEggEAIu44u62q5sVfzC7kytLi2Z/EzH2DKr4vDsoqDBeSZ71aRku/uSrjyiO4lyoq9Kva+eBAyjBay5fnqPVBaU3Rud2pdEoZEoyofi02jn4hxUKpAO1W0AUgsQolGe53qOdM4U8RbwnTR0gr3gp2mCd18pH3SRMP9ryrsBAxGzJ6mR3RgdZnlTlqVGXCeWUeVpbH+lcHw3uvd+o/xkvJ/3ypxz+rWILiAZ3QlCirzn/qb2fHuKf3VBh8RVFuQDaM5voajZlgjD6KzNCsbATOqOA6eJI4j0ngPdDlIjGHAnahuyluQ5f5SIaIjLC+ZeCOfIYni0MQ+BHO0JNbccjq2Unb7TBMBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBCYmAI0Ao3Ok1cSmVw0SgQGgCBK62z1r5RfRjf1xKfqDxTsGUHfsUmM3EjGJfnWzCRvuQ==]
        block: *blockStyle
        string: *stringStyle
        """
        simple_file = create_temp_yaml_file(tmp_path_factory, simple_content)
        anchored_file = create_temp_yaml_file(tmp_path_factory, anchored_content)
        
        result = script_runner.run(
            self.command,
            "--newprivatekey={}".format(new_eyaml_keys[0]),
            "--newpublickey={}".format(new_eyaml_keys[1]),
            "--oldprivatekey={}".format(old_eyaml_keys[0]),
            "--oldpublickey={}".format(old_eyaml_keys[1]),
            simple_file,
            anchored_file
        )
        assert result.success, result.stderr

        with open(simple_file, 'r') as fhnd:
            simple_data = fhnd.read()

        with open(anchored_file, 'r') as fhnd:
            anchored_data = fhnd.read()

        assert not simple_data == simple_content
        assert not anchored_data == anchored_content

        # FIXME:  Verify that block and string formatting is correct

    def test_yaml_parsing_error(self, script_runner, imparsible_yaml_file, old_eyaml_keys, new_eyaml_keys):
        result = script_runner.run(
            self.command,
            "--newprivatekey={}".format(new_eyaml_keys[0]),
            "--newpublickey={}".format(new_eyaml_keys[1]),
            "--oldprivatekey={}".format(old_eyaml_keys[0]),
            "--oldpublickey={}".format(old_eyaml_keys[1]),
            imparsible_yaml_file
        )
        assert not result.success, result.stderr
        assert "YAML parsing error" in result.stderr

    def test_yaml_syntax_error(self, script_runner, badsyntax_yaml_file, old_eyaml_keys, new_eyaml_keys):
        result = script_runner.run(
            self.command,
            "--newprivatekey={}".format(new_eyaml_keys[0]),
            "--newpublickey={}".format(new_eyaml_keys[1]),
            "--oldprivatekey={}".format(old_eyaml_keys[0]),
            "--oldpublickey={}".format(old_eyaml_keys[1]),
            badsyntax_yaml_file
        )
        assert not result.success, result.stderr
        assert "YAML syntax error" in result.stderr

    def test_yaml_composition_error(self, script_runner, badcmp_yaml_file, old_eyaml_keys, new_eyaml_keys):
        result = script_runner.run(
            self.command,
            "--newprivatekey={}".format(new_eyaml_keys[0]),
            "--newpublickey={}".format(new_eyaml_keys[1]),
            "--oldprivatekey={}".format(old_eyaml_keys[0]),
            "--oldpublickey={}".format(old_eyaml_keys[1]),
            badcmp_yaml_file
        )
        assert not result.success, result.stderr
        assert "YAML composition error" in result.stderr

    def test_corrupted_eyaml_value(self, script_runner, tmp_path_factory, old_eyaml_keys, new_eyaml_keys):
        content = """---
        key: >
            ENC[PKCS7,MII ... corrupted-value ...
            DBAEqBBAwcy7jvcOGcMfLEtugGVWWUnWq1DJ4Q==]
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--newprivatekey={}".format(new_eyaml_keys[0]),
            "--newpublickey={}".format(new_eyaml_keys[1]),
            "--oldprivatekey={}".format(old_eyaml_keys[0]),
            "--oldpublickey={}".format(old_eyaml_keys[1]),
            yaml_file
        )
        assert not result.success, result.stderr
        assert "Unable to decrypt value!" in result.stderr

    def test_bad_recryption_key(self, script_runner, tmp_path_factory, old_eyaml_keys, new_eyaml_keys):
        content = """---
        key: >
          ENC[PKCS7,MIIBmQYJKoZIhvcNAQcDoIIBijCCAYYCAQAxggEhMIIBHQIBADAFMAACAQEw
          DQYJKoZIhvcNAQEBBQAEggEAs+8byhxSVFkzPAfGFazxsifEJQO3RH5MNf2g
          o/x0oh+y1SB6bwB/lPtCBnCwDgKUKR8VzqWM8sTYkLTkSWq5BxS+Hix0zL1u
          zqdzNbuFDNS3PoUM4XaBRPOhGL/xUGc8EuUmdc3RaGRqisZvqACAMDDMme5m
          sCJVHw/QC//hAH6zrPmPA8D5S6ibMHGURifqTmLvi1BxxzMIWXWBmRpadAaq
          nYqhYsI/IWyQBmF7OAwsREREu+qEiDDBOS5IchDcDnlxtoooB5xin4HDS9ED
          MJMlKfpB1FCNtrC4RJz4uqFuwvX482cct3TtS+/UrPLP7rm6EILs7QSQGsdM
          G+8k8DBcBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBD+Bx88oA/j57i5UB5U
          BHEogDDpFaKbtiGSTxOK44MpjLOGCZ4ME6lJz5EYVJQ3VJw95z98mvj6CgzL
          NI/TSIF7M9U=]
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--newprivatekey={}".format(new_eyaml_keys[1]),
            "--newpublickey={}".format(new_eyaml_keys[0]),
            "--oldprivatekey={}".format(old_eyaml_keys[0]),
            "--oldpublickey={}".format(old_eyaml_keys[1]),
            yaml_file
        )
        assert not result.success, result.stderr
        assert "unable to encrypt" in result.stderr

    def test_backup_file(self, script_runner, tmp_path_factory, old_eyaml_keys, new_eyaml_keys):
        import os

        content = """---
        key: >
          ENC[PKCS7,MIIBiQYJKoZIhvcNAQcDoIIBejCCAXYCAQAxggEhMIIBHQIBADAFMAACAQEw
          DQYJKoZIhvcNAQEBBQAEggEAPGA1g1Wx50RK8F/Y118w1VT/SnCa7PMfN2OM
          d82vGeWXm6INmoURMDWEvBUEFCmGZoOMLVlK3LALtUcPEW1N9ztJTypBrqqI
          1K8L9aZWRNFt7uwsaoHWvk1XjMujP+nn2ZO3OiFYkiWFh0PcFw7cT1TmexB4
          cNbBtNi7oJ88L17/8rbtJW465cWyj0pPCmwo3OvK39JcuJ2xosujNk4u5AUf
          TjWwklk3yjPvjG6AvoS4TK+vkmqUcCkyy0tLZR8Xu+3IzYCq+DYH4QBrrrZf
          pKer9VawzMzxgVXeCgKGEsa3XeSzWtgbyoZVtoBdl3uv2f8rGi5qAlwZ9syO
          Aold9zBMBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBDGUmDGJfp2Iqn7bATf
          r0H9gCBNamGg9iiM92wGcVSkNmGJtVk8yEe3EOVn/QNzQ6v0fw==]
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        backup_file = yaml_file + ".bak"
        result = script_runner.run(
            self.command,
            "--newprivatekey={}".format(new_eyaml_keys[0]),
            "--newpublickey={}".format(new_eyaml_keys[1]),
            "--oldprivatekey={}".format(old_eyaml_keys[0]),
            "--oldpublickey={}".format(old_eyaml_keys[1]),
            "--backup",
            yaml_file
        )
        assert result.success, result.stderr
        assert os.path.isfile(backup_file)

        with open(backup_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == content

    def test_replace_backup_file(self, script_runner, tmp_path_factory, old_eyaml_keys, new_eyaml_keys):
        import os

        content = """---
        key: >
          ENC[PKCS7,MIIBiQYJKoZIhvcNAQcDoIIBejCCAXYCAQAxggEhMIIBHQIBADAFMAACAQEw
          DQYJKoZIhvcNAQEBBQAEggEAPGA1g1Wx50RK8F/Y118w1VT/SnCa7PMfN2OM
          d82vGeWXm6INmoURMDWEvBUEFCmGZoOMLVlK3LALtUcPEW1N9ztJTypBrqqI
          1K8L9aZWRNFt7uwsaoHWvk1XjMujP+nn2ZO3OiFYkiWFh0PcFw7cT1TmexB4
          cNbBtNi7oJ88L17/8rbtJW465cWyj0pPCmwo3OvK39JcuJ2xosujNk4u5AUf
          TjWwklk3yjPvjG6AvoS4TK+vkmqUcCkyy0tLZR8Xu+3IzYCq+DYH4QBrrrZf
          pKer9VawzMzxgVXeCgKGEsa3XeSzWtgbyoZVtoBdl3uv2f8rGi5qAlwZ9syO
          Aold9zBMBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBDGUmDGJfp2Iqn7bATf
          r0H9gCBNamGg9iiM92wGcVSkNmGJtVk8yEe3EOVn/QNzQ6v0fw==]
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        backup_file = yaml_file + ".bak"
        with open(backup_file, 'w') as fhnd:
            fhnd.write(content + "\nkey2: plain scalar string value")

        result = script_runner.run(
            self.command,
            "--newprivatekey={}".format(new_eyaml_keys[0]),
            "--newpublickey={}".format(new_eyaml_keys[1]),
            "--oldprivatekey={}".format(old_eyaml_keys[0]),
            "--oldpublickey={}".format(old_eyaml_keys[1]),
            "--backup",
            yaml_file
        )
        assert result.success, result.stderr
        assert os.path.isfile(backup_file)

        with open(backup_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == content
