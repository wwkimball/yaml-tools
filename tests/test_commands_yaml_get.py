import pytest

from tests.conftest import create_temp_yaml_file


class Test_yaml_get():
    """Tests for the yaml-get command-line interface."""
    command = "yaml-get"

    def test_no_options(self, script_runner):
        result = script_runner.run(self.command)
        assert not result.success, result.stderr
        assert "the following arguments are required: -p/--query, YAML_FILE" in result.stderr

    def test_no_input_file(self, script_runner):
        result = script_runner.run(self.command, "--query='/test'")
        assert not result.success, result.stderr
        assert "the following arguments are required: YAML_FILE" in result.stderr

    def test_bad_input_file(self, script_runner):
        result = script_runner.run(self.command, "--query='/test'", "no-such-file")
        assert not result.success, result.stderr
        assert "YAML_FILE not found:" in result.stderr

    def test_no_query(self, script_runner, tmp_path_factory):
        content = """---
        no: ''
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(self.command, yaml_file)
        assert not result.success, result.stderr
        assert "the following arguments are required: -p/--query" in result.stderr

    def test_bad_privatekey(self, script_runner, tmp_path_factory):
        content = """---
        no: ''
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(self.command, "--query=aliases", "--privatekey=no-such-file", yaml_file)
        assert not result.success, result.stderr
        assert "EYAML private key is not a readable file" in result.stderr

    def test_bad_publickey(self, script_runner, tmp_path_factory):
        content = """---
        no: ''
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(self.command, "--query=aliases", "--publickey=no-such-file", yaml_file)
        assert not result.success, result.stderr
        assert "EYAML public key is not a readable file" in result.stderr

    def test_yaml_parsing_error(self, script_runner, imparsible_yaml_file):
        result = script_runner.run(self.command, "--query=/", imparsible_yaml_file)
        assert not result.success, result.stderr
        assert "YAML parsing error" in result.stderr

    def test_yaml_syntax_error(self, script_runner, badsyntax_yaml_file):
        result = script_runner.run(self.command, "--query=/", badsyntax_yaml_file)
        assert not result.success, result.stderr
        assert "YAML syntax error" in result.stderr

    def test_yaml_composition_error(self, script_runner, badcmp_yaml_file):
        result = script_runner.run(self.command, "--query=/", badcmp_yaml_file)
        assert not result.success, result.stderr
        assert "YAML composition error" in result.stderr

    def test_bad_yaml_path(self, script_runner, tmp_path_factory):
        content = """---
        aliases:
          - &plainScalar Plain scalar string
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(self.command, "--query=aliases[1]", yaml_file)
        assert not result.success, result.stderr
        assert "Required YAML Path does not match any nodes" in result.stderr

    def test_bad_eyaml_value(self, script_runner, tmp_path_factory):
        content = """---
        aliases:
          - &encryptedScalar >
            ENC[PKCS7,MIIx...broken-on-purpose...==]
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--query=aliases[&encryptedScalar]",
            "--eyaml=/does/not/exist-on-most/systems",
            yaml_file
        )
        assert not result.success, result.stderr
        assert "No accessible eyaml command" in result.stderr

    def test_query_anchor(self, script_runner, tmp_path_factory):
        content = """---
        aliases:
          - &plainScalar Plain scalar string
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(self.command, "--query=aliases[&plainScalar]", yaml_file)
        assert result.success, result.stderr
        assert "Plain scalar string" in result.stdout

    def test_query_list(self, script_runner, tmp_path_factory):
        content = """---
        aliases:
          - &plainScalar Plain scalar string
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(self.command, "--query=aliases", yaml_file)
        assert result.success, result.stderr
        assert '["Plain scalar string"]' in result.stdout
