import pytest

from tests.conftest import create_temp_yaml_file


class Test_yaml_paths():
    """Tests the yaml-paths command-line interface."""
    command = "yaml-paths"

    def test_no_options(self, script_runner):
        result = script_runner.run(self.command)
        assert not result.success, result.stderr
        assert "the following arguments are required: -s/--search, YAML_FILE" in result.stderr

    def test_no_input_file(self, script_runner):
        result = script_runner.run(self.command, "--search=%abc")
        assert not result.success, result.stderr
        assert "the following arguments are required: YAML_FILE" in result.stderr

    def test_bad_input_file(self, script_runner):
        result = script_runner.run(self.command, "--search=%abc", "no-such-file")
        assert not result.success, result.stderr
        assert "File not found:" in result.stderr

    def test_no_query(self, script_runner, tmp_path_factory):
        content = """---
        no: ''
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(self.command, yaml_file)
        assert not result.success, result.stderr
        assert "the following arguments are required: -s/--search" in result.stderr

    def test_yaml_parsing_error(self, script_runner, imparsible_yaml_file):
        result = script_runner.run(
            self.command, "--search=%abc", imparsible_yaml_file
        )
        assert not result.success, result.stderr
        assert "YAML parsing error" in result.stderr

    def test_yaml_syntax_error(self, script_runner, badsyntax_yaml_file):
        result = script_runner.run(
            self.command, "--search=%abc", badsyntax_yaml_file
        )
        assert not result.success, result.stderr
        assert "YAML syntax error" in result.stderr

    def test_yaml_composition_error(self, script_runner, badcmp_yaml_file):
        result = script_runner.run(
            self.command, "--search=%abc", badcmp_yaml_file
        )
        assert not result.success, result.stderr
        assert "YAML composition error" in result.stderr

    def test_bad_privatekey(self, script_runner, tmp_path_factory):
        content = """---
        no: ''
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--search=%abc", "--privatekey=no-such-file", yaml_file
        )
        assert not result.success, result.stderr
        assert "EYAML private key is not a readable file" in result.stderr

    def test_bad_publickey(self, script_runner, tmp_path_factory):
        content = """---
        no: ''
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--search=%abc", "--publickey=no-such-file", yaml_file
        )
        assert not result.success, result.stderr
        assert "EYAML public key is not a readable file" in result.stderr

    def test_simple_array_result(self, script_runner, tmp_path_factory):
        content = """---
        - element 1
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--search", "^element", yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join([
            "/[0]",
        ]) + "\n" == result.stdout

    def test_nonrepeating_value_anchored_array(self, script_runner, tmp_path_factory):
        content = """---
        aliases:
          - &anchor1 element 1

        array:
          - *anchor1
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--search", "^element", yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join([
            "/aliases[&anchor1]",
        ]) + "\n" == result.stdout

    def test_nonrepeating_anchor_name_in_array(self, script_runner, tmp_path_factory):
        content = """---
        aliases:
          - &anchor1 element 1

        array:
          - *anchor1
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--pathsep=/", "--refnames",
            "--search", "^anchor",
            yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join([
            "/aliases[&anchor1]"
        ]) + "\n" == result.stdout

    def test_nonrepeating_subarray(self, script_runner, tmp_path_factory):
        content = """---
        array:
          -
            - subvalue
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--search", "=subvalue", yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join([
            "/array[0][0]",
        ]) + "\n" == result.stdout

    def test_simple_hash_result(self, script_runner, tmp_path_factory):
        content = """---
        parent:
          child: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--search", "=value", yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join([
            "/parent/child",
        ]) + "\n" == result.stdout

    def test_ignore_aliases(self, script_runner, tmp_path_factory):
        content = """---
        aliases:
          - &anchoredValue Anchored value
        parent:
          child: *anchoredValue
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--search", "$alue", yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join([
            "/aliases[&anchoredValue]",
        ]) + "\n" == result.stdout

    def test_hash_merge_anchor(self, script_runner, tmp_path_factory):
        content = """---
        anchored_hash: &anchoredHash
          key: value
        more_hash:
          <<: *anchoredHash
          more: values
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--keynames", "--refnames",
            "--search", "^anchored", yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join([
            "/anchored_hash",
        ]) + "\n" == result.stdout

    def test_anchored_hash_value(self, script_runner, tmp_path_factory):
        content = """---
        hash:
          key: &anchoredValue anchored_value
          more: *anchoredValue
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--refnames",
            "--search", "^anchored", yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join([
            "/hash/key",
        ]) + "\n" == result.stdout

    def test_duplicate_hash_value_anchor(self, script_runner, tmp_path_factory):
        content = """---
        aliases:
          - &anchor element 1
        hash:
          child1: *anchor
          subhash:
            subchild1: *anchor
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--allowaliases",
            "--search", "^element", yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join([
            "/aliases[&anchor]",
            "/hash/child1",
            "/hash/subhash/subchild1",
        ]) + "\n" == result.stdout

    def test_simple_hash_anchor(self, script_runner, tmp_path_factory):
        content = """---
        parent: &anchored
          child: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--pathsep=/", "--refnames", "--keynames",
            "--search", "=anchored",
            yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join([
            "/parent",
        ]) + "\n" == result.stdout

    def test_hash_anchored_key(self, script_runner, tmp_path_factory):
        content = """---
        anchorKeys:
          &keyOne aliasOne: 11A1
          &keyTwo aliasTwo: 22B2
          &recursiveAnchorKey subjectKey: *recursiveAnchorKey

        hash:
          *keyOne :
            subval: 1.1
          *keyTwo :
            subval: 2.2
          *recursiveAnchorKey :
            subval: 3.3
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--onlykeynames",
            "--search", "=aliasOne", yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join([
            "/anchorKeys/aliasOne",
            "/hash/aliasOne",
        ]) + "\n" == result.stdout

    def test_hash_nonduplicate_anchor_name_search(self, script_runner, tmp_path_factory):
        content = """---
        anchorKeys:
          &keyOne aliasOne: 11A1
          &keyTwo aliasTwo: 22B2
          &recursiveAnchorKey subjectKey: *recursiveAnchorKey

        hash:
          *keyOne :
            subval: 1.1
          *keyTwo :
            subval: 2.2
          *recursiveAnchorKey :
            subval: 3.3
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/",
            "--refnames", "--keynames",
            "--anchorsonly",
            "--search", "=recursiveAnchorKey", yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join([
            "/anchorKeys/subjectKey",
        ]) + "\n" == result.stdout

    def test_hash_duplicate_anchor_name_search(self, script_runner, tmp_path_factory):
        content = """---
        anchorKeys:
          &keyOne aliasOne: 11A1
          &keyTwo aliasTwo: 22B2
          &recursiveAnchorKey subjectKey: *recursiveAnchorKey

        hash:
          *keyOne :
            subval: 1.1
          *keyTwo :
            subval: 2.2
          *recursiveAnchorKey :
            subval: 3.3
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--refnames", "--keynames",
            "--allowaliases", "--search", "=recursiveAnchorKey", yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join([
            "/anchorKeys/subjectKey",
            "/hash/subjectKey",
        ]) + "\n" == result.stdout

    def test_empty_search_expression(self, script_runner, tmp_path_factory):
        content = """---
        no: ''
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--search==", yaml_file
        )
        assert not result.success, result.stderr
        assert "An EXPRESSION with only a search operator has no effect" in result.stderr

    def test_bad_expression(self, script_runner, tmp_path_factory):
        content = """---
        no: ''
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--search=abc", yaml_file
        )
        assert not result.success, result.stderr
        assert "Invalid search expression" in result.stderr

    def test_bad_yamlpath(self, script_runner, tmp_path_factory):
        content = """---
        no: ''
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--search", "=](.", yaml_file
        )
        assert not result.success, result.stderr
        assert "Invalid search expression" in result.stderr

    def test_multi_search_expressions(self, script_runner, tmp_path_factory):
        content = """---
        - node: 1
          value: A
        - node: 2
          value: B
          nest:
            - alpha
            - bravo
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--pathsep=/", "--keynames",
            "--search", "^value",
            "--search", "=bravo",
            yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join([
            "[^value]: /[0]/value",
            "[^value]: /[1]/value",
            "[=bravo]: /[1]/nest[1]"
        ]) + "\n" == result.stdout

    def test_multi_file_single_expression_search(self, script_runner, tmp_path_factory):
        content1 = """---
        - node: 1
          value: A
        """
        content2 = """---
        - node: 2
          value: B
        """
        yaml_file1 = create_temp_yaml_file(tmp_path_factory, content1)
        yaml_file2 = create_temp_yaml_file(tmp_path_factory, content2)
        result = script_runner.run(
            self.command,
            "--pathsep=/", "--keynames",
            "--search", "^value",
            yaml_file1, yaml_file2
        )
        assert result.success, result.stderr
        assert "\n".join([
            "{}: /[0]/value".format(yaml_file1),
            "{}: /[0]/value".format(yaml_file2),
        ]) + "\n" == result.stdout

    def test_multi_file_multi_expression_search(self, script_runner, tmp_path_factory):
        content1 = """---
        - node: 1
          value: A
        """
        content2 = """---
        - node: 2
          value: B
          nest:
            - alpha
            - bravo
        """
        yaml_file1 = create_temp_yaml_file(tmp_path_factory, content1)
        yaml_file2 = create_temp_yaml_file(tmp_path_factory, content2)
        result = script_runner.run(
            self.command,
            "--pathsep=/", "--keynames",
            "--search", "^value",
            "--search", "=bravo",
            yaml_file1, yaml_file2
        )
        assert result.success, result.stderr
        assert "\n".join([
            "{}[^value]: /[0]/value".format(yaml_file1),
            "{}[^value]: /[0]/value".format(yaml_file2),
            "{}[=bravo]: /[0]/nest[1]".format(yaml_file2)
        ]) + "\n" == result.stdout

    def test_multi_file_multi_expression_pathonly_search(self, script_runner, tmp_path_factory):
        content1 = """---
        - node: 1
          value: A
        """
        content2 = """---
        - node: 2
          value: B
          nest:
            - alpha
            - bravo
        """
        yaml_file1 = create_temp_yaml_file(tmp_path_factory, content1)
        yaml_file2 = create_temp_yaml_file(tmp_path_factory, content2)
        result = script_runner.run(
            self.command,
            "--pathsep=/", "--keynames", "--pathonly",
            "--search", "^value",
            "--search", "=bravo",
            yaml_file1, yaml_file2
        )
        assert result.success, result.stderr
        assert "\n".join([
            "{}: /[0]/value".format(yaml_file1),
            "{}: /[0]/value".format(yaml_file2),
            "{}: /[0]/nest[1]".format(yaml_file2)
        ]) + "\n" == result.stdout

    def test_result_exclusions(self, script_runner, tmp_path_factory):
        content = """---
        accounts:
          - username: admin
            password: 12345
          - username: nonadmin
            password: password
        applications:
          app1:
            accounts:
              admin:
                user: admin
                passphrase: a passphrase is a password with spaces
              user1:
                user: passimion
                passphrase: ignores user because --onlykeynames
            links:
              gateway: 192.168.0.0/16
              passthrough: yes
          app2:
            display_name:  What a pass!
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--pathsep=/", "--onlykeynames",
            "--search", "%pass",
            "--except", "%passthrough",
            "--except", "%display",
            yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join([
            "/accounts[0]/password",
            "/accounts[1]/password",
            "/applications/app1/accounts/admin/passphrase",
            "/applications/app1/accounts/user1/passphrase",
        ]) + "\n" == result.stdout

    def test_empty_exclusion(self, script_runner, tmp_path_factory):
        content = """---
        key: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--pathsep=/",
            "--search==value",
            "--except==",
            yaml_file
        )
        assert not result.success, result.stderr
        assert "An EXPRESSION with only a search operator has no effect" in result.stderr
        assert "\n".join([
            "/key",
        ]) + "\n" in result.stdout

    def test_search_encrypted_values(self, script_runner, tmp_path_factory, old_eyaml_keys):
        content = """---
        aliases:
          - &doesNotMatch >
            ENC[PKCS7,MIIBiQYJKoZIhvcNAQcDoIIBejCCAXYCAQAxggEhMIIBHQIBADAFMAACAQEw
            DQYJKoZIhvcNAQEBBQAEggEAMjjCGsU40xyRcwMIEUOHxAcwftmvKCiMsZxk
            cLgp7tc52f+dNdymNDrfh6Q9LasFZZe6e7gzSjukVj9URZQkDDl7csAcLgIU
            MhladFC30XgNHdejogyXLm3ZEISXRGWuYWCldMz8SgXKdjh53lrjup4vq+30
            oj0l63Ayvx713lwMqO1wfpqX2gOJUcsobSNVXZ5a/j7pbqlgazaJjw859ZzJ
            l/PeunPHtfM987TX+sLb3gNoCmEer6DTgP9OH/mcvOog032QqADaBXSa5NCD
            b+wf5eYYEn3/FlgVZlTse865JAlDB+xcE0UoJtBt2qqOQcqVxWMKTahVdcMA
            fbUDqTBMBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBA+cYFas5DLzK18/KwN
            lR5igCCdj/rltHjF5wh/zf0wC9OxImzBIWRsJFiTU7cdN6cndg==]
          - &doesMatch >
            ENC[PKCS7,MIIBiQYJKoZIhvcNAQcDoIIBejCCAXYCAQAxggEhMIIBHQIBADAFMAACAQEw
            DQYJKoZIhvcNAQEBBQAEggEAoxeZnZUr27Uf0joVgiIzeTSGGWYIv/YMCVyH
            dqe0jvIrSjjg2ShQjPBe+syXKTeKZryU+eyuL5BmSBKXxhT9DNh89n2KpUwL
            euY+zDmIhzC2kaYpk3So2BKcf1U083xzVQi0tHQ6hnaddx/fSMocaO8eX9jO
            itSfVIuEylGNdH/HtZ8BtMz7t7AsnAiSTpkqx3BfBXbE7UDy5zEofnz9JwTr
            M1Hr7/E4ggi+oWXi+KKFmboVgRdTvN16F0/3v8IzytfkXMcKmaY2EbvVPc6X
            aUlBv7lav7iHXdtETMpVP5i04BGVNMaejd6Ij8O0j6pnAIZWPzFtmp/GIM3k
            uZ8FKTBMBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBDErMS1u80DI+6I3tXH
            0383gCBxoEtDQ9n93/oYDStliDn7/hOGOgwCExaIHRXxeMHLrg==]
        also_matches: >
          ENC[PKCS7,MIIBeQYJKoZIhvcNAQcDoIIBajCCAWYCAQAxggEhMIIBHQIBADAFMAACAQEw
          DQYJKoZIhvcNAQEBBQAEggEAgaYgoKqf77s8S8yfb6bvhrbubtym67/DkltB
          em0rN4Z2MVKgVp02wJKuaEX8L4DEftROgAz3TDqJihwcGXqMryr15OfRF7wM
          VLdqkD0+iRwqOWCoVIwFrJjquO/FyyaCeCNVH0XUjvJQyyUzokaHo9Jw6oqC
          9wx5GytBmGtoiniUJgHaetiDQ6OBYXufqNYGZMKJN1u1qJqnYnw+kJMnfoND
          SENEi0bRc9hufCNTCT1cuJolxQYCfhpbWPSQFfIWjrIguF3Yud7CRfCc8AFy
          NSk+MYcrYNJxpF4OPCdFS3KdGAKQrbUVMTzp8IJ6Sd9WLOKIM/+84nFoZaQ3
          KyhLjDA8BgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBDaeiqnwlecngAcBJlO
          8OvCgBDvP5ZkrDJjHj6N5T8wSl/0]
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--pathsep=/",
            "--search", "%what",
            "--decrypt",
            "--privatekey={}".format(old_eyaml_keys[0]),
            "--publickey={}".format(old_eyaml_keys[1]),
            yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join([
            "/aliases[&doesMatch]",
            "/also_matches",
        ]) + "\n" == result.stdout

    def test_dedupe_results(self, script_runner, tmp_path_factory):
        content = """---
        key: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--pathsep=/", "--keynames", "--pathonly",
            "--search", "=key",
            "--search", "=value",
            yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join([
            "/key",
        ]) + "\n" == result.stdout

    def test_expand_map_parents(self, script_runner, tmp_path_factory):
        content = """---
        parent1:
          child1.1: value1.1
          child1.2: value1.2
        parent2:
          child2.1:
            child2.1.1:
              child2.1.1.1: value2.1.1.1
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--pathsep=/",
            "--expand", "--keynames",
            "--search", "^parent",
            yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join([
            "/parent1/child1.1",
            "/parent1/child1.2",
            "/parent2/child2.1/child2.1.1/child2.1.1.1",
        ]) + "\n" == result.stdout

    @pytest.mark.parametrize("aliasmode,assertions", [
        ("--anchorsonly", [
            "/config/settings/overrides/static",
            "/config/accounts/overrides/root/name",
            "/config/accounts/overrides/root/pass",
            "/config/global/overrides/environment/PATH",
        ]),
        ("--allowvaluealiases", [
            "/config/settings/overrides/static",
            "/config/settings/overrides/default_pass",
            "/config/accounts/overrides/root/name",
            "/config/accounts/overrides/root/pass",
            "/config/accounts/defaults/globaladmin/name",
            "/config/accounts/defaults/globaladmin/pass",
            "/config/global/overrides/environment/PATH",
        ]),
        ("--allowkeyaliases", [
            "/config/settings/overrides/setting",
            "/config/settings/overrides/static",
            "/config/settings/defaults/setting",
            "/config/settings/someCustomerName/setting",
            "/config/settings/anotherCustomerName/setting",
            "/config/accounts/overrides/root/name",
            "/config/accounts/overrides/root/pass",
            "/config/accounts/defaults/globaladmin/name",
            "/config/accounts/defaults/globaladmin/pass",
            "/config/accounts/someCustomerName/admin/name",
            "/config/accounts/anotherCustomerName/admin/name",
            "/config/global/setting",
            "/config/global/overrides/environment/PATH",
        ]),
        ("--allowaliases", [
            "/config/settings/overrides/setting",
            "/config/settings/overrides/static",
            "/config/settings/overrides/default_pass",
            "/config/settings/defaults/setting",
            "/config/settings/someCustomerName/setting",
            "/config/settings/anotherCustomerName/setting",
            "/config/accounts/overrides/root/name",
            "/config/accounts/overrides/root/pass",
            "/config/accounts/defaults/globaladmin/name",
            "/config/accounts/defaults/globaladmin/pass",
            "/config/accounts/someCustomerName/admin/name",
            "/config/accounts/someCustomerName/admin/pass",
            "/config/accounts/anotherCustomerName/admin/name",
            "/config/accounts/anotherCustomerName/admin/pass",
            "/config/global/setting",
            "/config/global/overrides/environment/PATH",
        ]),
    ])
    def test_expanded_keymatch_aliases(self, script_runner, tmp_path_factory, aliasmode, assertions):
        content = """---
        aliases:
          # Keys:
          - &customer1 someCustomerName: Some Customer Name
          - &customer2 anotherCustomerName: Another Customer Name
          - &settingName setting

          # Values:
          - &defaultPassphrase CHANGE ME!

        settings: &allSettings
          defaults:
            *settingName : default
          *customer1 :
            *settingName : one
          *customer2 :
            *settingName : another

        accounts: &allAccounts
          defaults:
            globaladmin:
              name: user0
              pass: >
                ENC[PKCS7,MIIBiQYJKoZIhvcNAQcDoIIBejCCAXYCAQAxggEhMIIBHQIBADAFMAACAQEw
                DQYJKoZIhvcNAQEBBQAEggEAfyvl69TDxQgS4Gon3gw57W8McgYGFsbh+N2e
                EHdoOG5nR1NpKdL1px+csX6qbKgeolCBsQUADPn6x3aiyjIK754MSASthWmu
                glJzJlGvDeRRoXj8leuGPYAsEH59zmFe6rjVZOq57XP45zpq9/ggcvivzrFP
                9zBcIq/3ITnoMLhjpMkENcn1qbYeLXTJXbLhd5WXK47epngtY2Od89TkkquU
                is464XYQ4kv0JRm1K01DdLcKeIpuOXhDAQJ7f/Tmbn1dUYtNzJKBSsNW1fW1
                2Taf6IcCcrGkqcYmw61z/wbTcCVJj/ihBjgaPzhz16WEOHz/qZ666eVfo8tg
                bI54MTBMBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBCeVE0neevYnLy9UMgl
                f0YugCDjDxDCkIrSpQWCcUA5RHZyOngXMrbOJqlw92d21WDZXg==]
          *customer1 :
            admin:
              name: user1
              pass: *defaultPassphrase
          *customer2 :
            admin:
              name: user2
              pass: *defaultPassphrase

        config:
          settings:
            <<: *allSettings
            overrides:
              *settingName : absolute
              static: value
              default_pass: *defaultPassphrase
          accounts:
            <<: *allAccounts
            overrides:
              root:
                name: root
                pass: >
                  ENC[PKCS7,MIIBmQYJKoZIhvcNAQcDoIIBijCCAYYCAQAxggEhMIIBHQIBADAFMAACAQEw
                  DQYJKoZIhvcNAQEBBQAEggEAhxT9HVAYbxtCDFj9kOKqnHXvZUUL0m43c86B
                  KTkIWwhaRtdy5lTHYqTuDxs1TV+3N+0FILhu9+EkAu+af8lbPP6dDrxk5rqw
                  6GsuoO3/4hU5JiqBHoJ/0V4cSL3wkBBtcoLgh+5nu/mFfPkbU1QCgKFTIHgc
                  fy4izEN8jQi+mf3kThCHyN6sezbzlSfbj4qjnNbnXTFBpRrbuZUGRkaO0tRd
                  pwuZIdtOA0l5jz+iFGXCJYy+WY6ipGSOV7ecbfMUrZdq0wM69oZuAda6RXoP
                  S8JdOCrspCkkkRMO8gijUH38ONlY8aK9EdIN0OJlAqw2MZoVPrd1yx2OloP2
                  NY3tZjBcBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBBcACTjY0bIdZxtSdZj
                  v74ngDDa4+WAkqQjW9UuRmz60HvLdkr6QLUkGR0FIzXYfPNLMGvyJjcjqdba
                  kfk8ED1ScmA=]
          global:
            *settingName : everywhere
            overrides:
              environment:
                PATH: /usr/local/sbin:/usr/sbin:/sbin:/usr/local/bin:/usr/bin:/bin
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--pathsep=/",
            "--expand", "--keynames",
            aliasmode,
            "--search", "=config",
            yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join(assertions) + "\n" == result.stdout

    def test_expanded_key_refmatches(self, script_runner, tmp_path_factory):
        content = """---
        anchors:
            &keyAnchor key: &valueAnchor value
        *keyAnchor :
          ignoreChild: *valueAnchor
          includeChild: static
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--pathsep=/",
            "--expand", "--keynames",
            "--refnames", "--allowkeyaliases",
            "--search", "=keyAnchor",
            yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join([
            "/anchors/key",
            "/key/includeChild",
        ]) + "\n" == result.stdout

    def test_expanded_value_refmatches(self, script_runner, tmp_path_factory):
        content = """---
        copy: &thisHash
          key: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--pathsep=/",
            "--expand",
            "--refnames",
            "--search", "=thisHash",
            yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join([
            "/copy/key",
        ]) + "\n" == result.stdout

    def test_expand_sequence_parents(self, script_runner, tmp_path_factory):
        content = """---
        - &list
          -
            -
              - value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--pathsep=/",
            "--expand", "--refnames",
            "--search", "=list",
            yaml_file
        )
        assert result.success, result.stderr
        assert "\n".join([
            "/&list[0][0][0]",
        ]) + "\n" == result.stdout

    def test_yield_seq_children_direct(self, tmp_path_factory, quiet_logger):
        from yamlpath.enums import PathSeperators, PathSearchMethods
        from yamlpath.path import SearchTerms
        from yamlpath.func import get_yaml_data, get_yaml_editor
        from yamlpath.commands.yaml_paths import yield_children
        from itertools import zip_longest

        content = """---
        - &value Test value
        - value
        - *value
        """
        processor = get_yaml_editor()
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        yaml_data = get_yaml_data(processor, quiet_logger, yaml_file)
        seen_anchors = []
        assertions = ["/&value", "/[1]"]
        results = []
        for assertion, path in zip_longest(assertions, yield_children(
            quiet_logger, yaml_data,
            SearchTerms(False, PathSearchMethods.EQUALS, "*", "value"),
            PathSeperators.FSLASH, "", seen_anchors, search_anchors=True,
            include_aliases=False
        )):
            assert assertion == str(path)

    @pytest.mark.parametrize("include_aliases,assertions", [
        (False, ["/aliases[&aValue]", "/hash/key1", "/hash/key3"]),
        (True, ["/aliases[&aValue]", "/hash/key1", "/hash/key2", "/hash/key3"]),
    ])
    def test_yield_map_children_direct(self, tmp_path_factory, quiet_logger, include_aliases, assertions):
        from yamlpath.enums import PathSeperators, PathSearchMethods
        from yamlpath.path import SearchTerms
        from yamlpath.func import get_yaml_data, get_yaml_editor
        from yamlpath.commands.yaml_paths import yield_children
        from itertools import zip_longest

        content = """---
        aliases:
          - &aValue val2

        hash:
          key1: val1
          key2: *aValue
          key3: val3
        """
        processor = get_yaml_editor()
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        yaml_data = get_yaml_data(processor, quiet_logger, yaml_file)
        seen_anchors = []
        results = []
        for assertion, path in zip_longest(assertions, yield_children(
            quiet_logger, yaml_data,
            SearchTerms(False, PathSearchMethods.EQUALS, "*", "anchor"),
            PathSeperators.FSLASH, "", seen_anchors, search_anchors=True,
            include_value_aliases=include_aliases
        )):
            assert assertion == str(path)

    def test_yield_raw_children_direct(self, tmp_path_factory, quiet_logger):
        from yamlpath.enums import PathSeperators, PathSearchMethods
        from yamlpath.path import SearchTerms
        from yamlpath.func import get_yaml_data, get_yaml_editor
        from yamlpath.commands.yaml_paths import yield_children
        from itertools import zip_longest

        content = """some raw text value
        """
        processor = get_yaml_editor()
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        yaml_data = get_yaml_data(processor, quiet_logger, yaml_file)
        seen_anchors = []
        assertions = ["/"]
        results = []
        for assertion, path in zip_longest(assertions, yield_children(
            quiet_logger, yaml_data,
            SearchTerms(False, PathSearchMethods.STARTS_WITH, "*", "some"),
            PathSeperators.FSLASH, "", seen_anchors, search_anchors=False,
            include_key_aliases=False, include_value_aliases=False
        )):
            assert assertion == str(path)
