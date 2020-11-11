import pytest

from tests.conftest import create_temp_yaml_file


class Test_commands_yaml_merge():
    """Tests for the yaml-merge command-line tool."""
    command = "yaml-merge"

    def test_no_options(self, script_runner):
        result = script_runner.run(self.command, "--nostdin")
        assert not result.success, result.stderr
        assert "There must be at least one YAML_FILE" in result.stderr

    def test_missing_input_file_arg(self, script_runner):
        result = script_runner.run(self.command, "--nostdin", "no-file.yaml")
        assert not result.success, result.stderr
        assert "Not a file" in result.stderr

    def test_missing_config_file(self, script_runner):
        result = script_runner.run(
            self.command
            , "--config=no-file.ini"
            , "lhs-file.yaml"
            , "rhs-file.yaml")
        assert not result.success, result.stderr
        assert "INI style configuration file is not readable" in result.stderr

    def test_nothing_to_backup(self, script_runner):
        result = script_runner.run(self.command, "--nostdin", "--backup")
        assert not result.success, result.stderr
        assert "applies only to OVERWRITE file" in result.stderr

    def test_output_file_exists(self, script_runner, tmp_path_factory):
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
key: value
""")
        output_file = create_temp_yaml_file(tmp_path_factory, merged_yaml)

        result = script_runner.run(
            self.command
            , "--output={}".format(output_file)
            , "lhs-file.yaml"
            , "rhs-file.yaml")
        assert not result.success, result.stderr
        assert "Output file already exists" in result.stderr

    def test_missing_prime_input_file(self, script_runner):
        result = script_runner.run(
            self.command
            , "no-file.yaml"
            , "-")
        assert not result.success, result.stderr
        assert "Not a file" in result.stderr

    def test_missing_rhs_input_file(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
""")

        result = script_runner.run(
            self.command
            , lhs_file
            , "no-such-file.yaml")
        assert not result.success, result.stderr
        assert "Not a file" in result.stderr

    def test_empty_rhs_input_file(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, "")

        result = script_runner.run(
            self.command
            , "--nostdin"
            , lhs_file
            , rhs_file)
        assert result.success, result.stderr

    def test_merge_two_happy_files_to_stdout(
        self, script_runner, tmp_path, tmp_path_factory
    ):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  rhs_exclusive: RHS exclusive
  merge_target: RHS override value
""")
        merged_yaml_content = """---
hash:
  lhs_exclusive: LHS exclusive
  rhs_exclusive: RHS exclusive
  merge_target: RHS override value
"""

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--nostdin"
            , lhs_file
            , rhs_file)
        assert result.success, result.stderr
        assert merged_yaml_content == result.stdout

    def test_merge_two_happy_yaml_files_to_file(self, script_runner, tmp_path, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  rhs_exclusive: RHS exclusive
  merge_target: RHS override value
""")
        merged_yaml_content = """---
hash:
  lhs_exclusive: LHS exclusive
  rhs_exclusive: RHS exclusive
  merge_target: RHS override value
"""

        output_dir = tmp_path / "test_merge_two_happy_yaml_files_to_file"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Output File:  {}".format(output_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--nostdin"
            , "--output={}".format(output_file)
            , lhs_file
            , rhs_file)
        assert result.success, result.stderr

        with open(output_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert merged_yaml_content == filedat

    def test_merge_two_happy_multidoc_yaml_files_to_file(self, script_runner, tmp_path, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
...
---
hash:
  lhs2_exclusive: LHS2 exclusive
  merge2_target: LHS2 original value
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  rhs_exclusive: RHS exclusive
  merge_target: RHS override value
...
---
hash:
  rhs2_exclusive: RHS2 exclusive
  merge_target: RHS2 override value
  merge2_target: RHS2 2nd override value
""")
        merged_yaml_content = """---
hash:
  lhs_exclusive: LHS exclusive
  rhs2_exclusive: RHS2 exclusive
  rhs_exclusive: RHS exclusive
  merge_target: RHS2 override value
  lhs2_exclusive: LHS2 exclusive
  merge2_target: RHS2 2nd override value
"""

        output_dir = tmp_path / "test_merge_two_happy_multidoc_yaml_files_to_file"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Output File:  {}".format(output_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--nostdin"
            , "--output={}".format(output_file)
            , lhs_file
            , rhs_file)
        assert result.success, result.stderr

        with open(output_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert merged_yaml_content == filedat

    def test_merge_two_happy_json_files_to_file(self, script_runner, tmp_path, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """{
  "hash": {
      "lhs_exclusive": "LHS exclusive",
      "merge_target": "LHS original value"
  }
}
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """{
  "hash": {
      "rhs_exclusive": "RHS exclusive",
      "merge_target": "RHS override value"
  }
}
""")
        merged_yaml_content = """{"hash": {"lhs_exclusive": "LHS exclusive", "rhs_exclusive": "RHS exclusive", "merge_target": "RHS override value"}}"""

        output_dir = tmp_path / "test_merge_two_happy_json_files_to_file"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Output File:  {}".format(output_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--nostdin"
            , "--output={}".format(output_file)
            , "--document-format=json"
            , lhs_file
            , rhs_file)
        assert result.success, result.stderr

        with open(output_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert merged_yaml_content == filedat

    def test_convert_yaml_to_json_file(self, script_runner, tmp_path, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
""")
        merged_yaml_content = """{"hash": {"lhs_exclusive": "LHS exclusive", "merge_target": "LHS original value"}}"""

        output_dir = tmp_path / "test_convert_yaml_to_json_file"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("Output File:  {}".format(output_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--nostdin"
            , "--document-format=json"
            , "--output={}".format(output_file)
            , lhs_file)
        assert result.success, result.stderr

        with open(output_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert merged_yaml_content == filedat

    def test_convert_json_to_yaml_file(self, script_runner, tmp_path, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """{"hash": {"lhs_exclusive": "LHS exclusive", "merge_target": "LHS original value"}}""")
        merged_yaml_content = """---
"hash":
  "lhs_exclusive": "LHS exclusive"
  "merge_target": "LHS original value"
"""

        output_dir = tmp_path / "test_convert_yaml_to_json_file"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("Output File:  {}".format(output_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--nostdin"
            , "--document-format=yaml"
            , "--output={}".format(output_file)
            , lhs_file)
        assert result.success, result.stderr

        with open(output_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert merged_yaml_content == filedat

    def test_bad_rhs_input_file(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
- one
- two
""")

        result = script_runner.run(
            self.command
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr

    def test_bad_multidoc_rhs_input_file(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  rhs_exclusive: RHS exclusive
  merge_target: RHS override value
...
---
- one
- two
""")

        result = script_runner.run(
            self.command
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr

    def test_merge_explicit_from_stdin_to_stdout(
        self, script_runner, tmp_path_factory
    ):
        import subprocess

        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
""")
        rhs_content = ("{hash: {rhs_exclusive: RHS exclusive"
                       ", merge_target: RHS override value}}")
        merged_yaml_content = """---
hash:
  lhs_exclusive: LHS exclusive
  rhs_exclusive: RHS exclusive
  merge_target: RHS override value
"""

        result = subprocess.run(
            [self.command
            , lhs_file
            , "-"]
            , stdout=subprocess.PIPE
            , input=rhs_content
            , universal_newlines=True
        )

        # DEBUG
        # print("Expected:")
        # print(merged_yaml_content)
        # print("Got:")
        # print(result.stdout)

        assert 0 == result.returncode, result.stderr
        assert merged_yaml_content == result.stdout

    def test_merge_implicit_from_stdin_to_stdout_implicit_json(
        self, script_runner, tmp_path_factory
    ):
        import subprocess

        lhs_file = create_temp_yaml_file(tmp_path_factory, """{
  "hash": {
      "lhs_exclusive": "LHS exclusive",
      "merge_target": "LHS original value"
  }
}
""")
        rhs_content = """{
  "hash": {
      "rhs_exclusive": "RHS exclusive",
      "merge_target": "RHS override value"
  }
}
"""
        merged_yaml_content = """{"hash": {"lhs_exclusive": "LHS exclusive", "rhs_exclusive": "RHS exclusive", "merge_target": "RHS override value"}}"""

        result = subprocess.run(
            [self.command
            , lhs_file]
            , stdout=subprocess.PIPE
            , input=rhs_content
            , universal_newlines=True
        )

        # DEBUG
        # print("Expected:")
        # print(merged_yaml_content)
        # print("Got:")
        # print(result.stdout)

        assert 0 == result.returncode, result.stderr
        assert merged_yaml_content == result.stdout

    def test_merge_implicit_from_stdin_to_stdout_explicit_json(
        self, script_runner, tmp_path_factory
    ):
        import subprocess

        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
""")
        rhs_content = """---
hash:
  rhs_exclusive: RHS exclusive
  merge_target: RHS override value
"""
        merged_yaml_content = """{"hash": {"lhs_exclusive": "LHS exclusive", "rhs_exclusive": "RHS exclusive", "merge_target": "RHS override value"}}"""

        result = subprocess.run(
            [self.command
            , lhs_file
            , "--document-format=json"]
            , stdout=subprocess.PIPE
            , input=rhs_content
            , universal_newlines=True
        )

        # DEBUG
        # print("Expected:")
        # print(merged_yaml_content)
        # print("Got:")
        # print(result.stdout)

        assert 0 == result.returncode, result.stderr
        assert merged_yaml_content == result.stdout

    def test_bad_mergeat_yamlpath(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
new_key: New value
""")

        result = script_runner.run(
            self.command
            , "--mergeat=/[.~='']"
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert "Unexpected use of ~ operator" in result.stderr

    def test_too_many_pseudofiles(self, script_runner):
        result = script_runner.run(
            self.command
            , '-'
            , '-')
        assert not result.success, result.stderr
        assert "Only one YAML_FILE may be the - pseudo-file" in result.stderr

    def test_yaml_syntax_error(self, script_runner, badsyntax_yaml_file, old_eyaml_keys, new_eyaml_keys):
        result = script_runner.run(self.command, badsyntax_yaml_file)
        assert not result.success, result.stderr
        assert "YAML syntax error" in result.stderr

    def test_merge_yaml_output_json(self, script_runner, tmp_path, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &some_lhs_string A string value

lhs_anchored_hash: &some_lhs_hash
  with: properties
  of_its: own

hash:
  <<: *some_lhs_hash
  uses_an_alias: *some_lhs_string
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
...
---
aliases:
  - &some_rhs_number 5280

rhs_anchored_hash: &some_rhs_hash
  having: its
  very_own: properties

hash:
  <<: *some_rhs_hash
  uses_an_alias: *some_rhs_number
  rhs_exclusive: RHS exclusive
  merge_target: RHS override value
""")
        merged_yaml_content = """{"aliases": ["A string value", 5280], "lhs_anchored_hash": {"with": "properties", "of_its": "own"}, "rhs_anchored_hash": {"having": "its", "very_own": "properties"}, "hash": {"uses_an_alias": 5280, "lhs_exclusive": "LHS exclusive", "rhs_exclusive": "RHS exclusive", "merge_target": "RHS override value", "having": "its", "very_own": "properties"}}"""

        output_dir = tmp_path / "test_convert_yaml_to_json_file"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("Output File:  {}".format(output_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--nostdin"
            , "--document-format=json"
            , "--output={}".format(output_file)
            , lhs_file)
        assert result.success, result.stderr

        with open(output_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert merged_yaml_content == filedat

    def test_merge_happy_multi_single_yaml_files_to_file(self, script_runner, tmp_path, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &some_lhs_string A string value

lhs_anchored_hash: &some_lhs_hash
  with: properties
  of_its: own

hash:
  <<: *some_lhs_hash
  uses_an_alias: *some_lhs_string
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
...
---
hash:
  of_its: very own
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &some_rhs_number 5280

rhs_anchored_hash: &some_rhs_hash
  having: its
  very_own: properties

hash:
  <<: *some_rhs_hash
  uses_an_alias: *some_rhs_number
  rhs_exclusive: RHS exclusive
  merge_target: RHS override value
""")
        merged_yaml_content = """---
aliases:
  - &some_lhs_string A string value
  - &some_rhs_number 5280
lhs_anchored_hash: &some_lhs_hash
  with: properties
  of_its: own
rhs_anchored_hash: &some_rhs_hash
  having: its
  very_own: properties
hash:
  <<: [*some_lhs_hash, *some_rhs_hash]
  uses_an_alias: *some_rhs_number
  lhs_exclusive: LHS exclusive
  rhs_exclusive: RHS exclusive
  merge_target: RHS override value
  of_its: very own
"""

        output_dir = tmp_path / "test_merge_happy_multi_single_yaml_files_to_file"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Output File:  {}".format(output_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--nostdin"
            , "--output={}".format(output_file)
            , lhs_file
            , rhs_file)
        assert result.success, result.stderr

        with open(output_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert merged_yaml_content == filedat

    def test_backup_file(self, script_runner, tmp_path_factory):
        import os

        content = """---
        key: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        backup_file = yaml_file + ".bak"
        result = script_runner.run(
            self.command,
            "--nostdin",
            "--overwrite={}".format(yaml_file),
            "--backup",
            yaml_file
        )
        assert result.success, result.stderr
        assert os.path.isfile(backup_file)

        with open(backup_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == content

    def test_replace_backup_file(self, script_runner, tmp_path_factory):
        import os

        content = """---
        key: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        backup_file = yaml_file + ".bak"
        with open(backup_file, 'w') as fhnd:
            fhnd.write(content + "\nkey2: value2")

        result = script_runner.run(
            self.command,
            "--nostdin",
            "--overwrite={}".format(yaml_file),
            "--backup",
            yaml_file
        )
        assert result.success, result.stderr
        assert os.path.isfile(backup_file)

        with open(backup_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == content

    def test_append_scalar_to_array(
        self, script_runner, tmp_path_factory
    ):
        import subprocess

        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
an_array:
  - Element 0
  - Element 1
  - Element 2
""")
        rhs_content = "New Element"
        merged_yaml_content = """---
an_array:
  - Element 0
  - Element 1
  - Element 2
  - New Element
"""

        result = subprocess.run(
            [self.command
            , "--mergeat=/an_array"
            , lhs_file]
            , stdout=subprocess.PIPE
            , input=rhs_content
            , universal_newlines=True
        )

        # DEBUG
        # print("Expected:")
        # print(merged_yaml_content)
        # print("Got:")
        # print(result.stdout)

        assert 0 == result.returncode, result.stderr
        assert merged_yaml_content == result.stdout

    def test_append_empty_to_array(
        self, script_runner, tmp_path_factory
    ):
        import subprocess

        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
an_array:
  - Element 0
  - Element 1
  - Element 2
""")
        rhs_content = ""
        merged_yaml_content = """---
an_array:
  - Element 0
  - Element 1
  - Element 2
  - ''
"""

        result = subprocess.run(
            [self.command
            , "--mergeat=/an_array"
            , lhs_file]
            , stdout=subprocess.PIPE
            , input=rhs_content
            , universal_newlines=True
        )

        # DEBUG
        # print("Expected:")
        # print(merged_yaml_content)
        # print("Got:")
        # print(result.stdout)

        assert 0 == result.returncode, result.stderr
        assert merged_yaml_content == result.stdout

    def test_set_scalar_in_array(
        self, script_runner, tmp_path_factory
    ):
        import subprocess

        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
an_array:
  - Element 0
  - Element 1
  - Element 2
""")
        rhs_content = "New Element"
        merged_yaml_content = """---
an_array:
  - Element 0
  - New Element
  - Element 2
"""

        result = subprocess.run(
            [self.command
            , "--mergeat=/an_array[1]"
            , lhs_file]
            , stdout=subprocess.PIPE
            , input=rhs_content
            , universal_newlines=True
        )

        # DEBUG
        # print("Expected:")
        # print(merged_yaml_content)
        # print("Got:")
        # print(result.stdout)

        assert 0 == result.returncode, result.stderr
        assert merged_yaml_content == result.stdout

    def test_set_empty_in_array(
        self, script_runner, tmp_path_factory
    ):
        import subprocess

        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
an_array:
  - Element 0
  - Element 1
  - Element 2
""")
        rhs_content = ""
        merged_yaml_content = """---
an_array:
  - Element 0
  - ''
  - Element 2
"""

        result = subprocess.run(
            [self.command
            , "--mergeat=/an_array[1]"
            , lhs_file]
            , stdout=subprocess.PIPE
            , input=rhs_content
            , universal_newlines=True
        )

        # DEBUG
        # print("Expected:")
        # print(merged_yaml_content)
        # print("Got:")
        # print(result.stdout)

        assert 0 == result.returncode, result.stderr
        assert merged_yaml_content == result.stdout

    def test_append_scalar_to_hash(
        self, script_runner, tmp_path_factory
    ):
        import subprocess

        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
a_hash:
  key: value
""")
        rhs_content = "New Value"
        merged_yaml_content = """---
a_hash:
  key: value
  new_key: New Value
"""

        result = subprocess.run(
            [self.command
            , "--mergeat=/a_hash/new_key"
            , lhs_file]
            , stdout=subprocess.PIPE
            , input=rhs_content
            , universal_newlines=True
        )

        # DEBUG
        # print("Expected:")
        # print(merged_yaml_content)
        # print("Got:")
        # print(result.stdout)

        assert 0 == result.returncode, result.stderr
        assert merged_yaml_content == result.stdout

    def test_append_empty_to_hash(
        self, script_runner, tmp_path_factory
    ):
        import subprocess

        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
a_hash:
  key: value
""")
        rhs_content = ""
        merged_yaml_content = """---
a_hash:
  key: value
  new_key: ''
"""

        result = subprocess.run(
            [self.command
            , "--mergeat=/a_hash/new_key"
            , lhs_file]
            , stdout=subprocess.PIPE
            , input=rhs_content
            , universal_newlines=True
        )

        # DEBUG
        # print("Expected:")
        # print(merged_yaml_content)
        # print("Got:")
        # print(result.stdout)

        assert 0 == result.returncode, result.stderr
        assert merged_yaml_content == result.stdout

    def test_set_scalar_in_hash(
        self, script_runner, tmp_path_factory
    ):
        import subprocess

        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
a_hash:
  key: value
""")
        rhs_content = "New Value"
        merged_yaml_content = """---
a_hash:
  key: New Value
"""

        result = subprocess.run(
            [self.command
            , "--mergeat=/a_hash/key"
            , lhs_file]
            , stdout=subprocess.PIPE
            , input=rhs_content
            , universal_newlines=True
        )

        # DEBUG
        # print("Expected:")
        # print(merged_yaml_content)
        # print("Got:")
        # print(result.stdout)

        assert 0 == result.returncode, result.stderr
        assert merged_yaml_content == result.stdout

    def test_set_empty_in_hash(
        self, script_runner, tmp_path_factory
    ):
        import subprocess

        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
a_hash:
  key: value
""")
        rhs_content = ""
        merged_yaml_content = """---
a_hash:
  key: ''
"""

        result = subprocess.run(
            [self.command
            , "--mergeat=/a_hash/key"
            , lhs_file]
            , stdout=subprocess.PIPE
            , input=rhs_content
            , universal_newlines=True
        )

        # DEBUG
        # print("Expected:")
        # print(merged_yaml_content)
        # print("Got:")
        # print(result.stdout)

        assert 0 == result.returncode, result.stderr
        assert merged_yaml_content == result.stdout

    def test_tagged_value_merging(
        self, script_runner, tmp_path_factory
    ):
        import subprocess

        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &anchor_keeps_tag !tagged_scalar This anchored scalar keeps its tag.
  - &anchor_loses_tag !tagged_scalar This anchored scalar loses its tag.
  - &anchor_gains_tag This anchored scalar gains a tag.
  - &anchor_none_tag An anchored scalar with no tag.

hash_loses_tag: !hash_tag
  keeps_tag: *anchor_keeps_tag
  loses_tag: *anchor_loses_tag
  gains_tag: *anchor_gains_tag
  none_tag: *anchor_none_tag
  tag_none: Neither gains nor loses its tag.
  tag_keep: !tagged_scalar Keeps its tag.
  tag_adds: This value gains a tag.
  tag_drops: !tagged_scalar This value loses its tag.

hash_gains_tag:
  keeps_tag: *anchor_keeps_tag
  loses_tag: *anchor_loses_tag
  gains_tag: *anchor_gains_tag
  none_tag: *anchor_none_tag
  tag_none: Neither gains nor loses its tag.
  tag_keep: !tagged_scalar Keeps its tag.
  tag_adds: This value gains a tag.
  tag_drops: !tagged_scalar This value loses its tag.

hash_none_tag:
  keeps_tag: *anchor_keeps_tag
  loses_tag: *anchor_loses_tag
  gains_tag: *anchor_gains_tag
  none_tag: *anchor_none_tag
  tag_none: Neither gains nor loses its tag.
  tag_keep: !tagged_scalar Keeps its tag.
  tag_adds: This value gains a tag.
  tag_drops: !tagged_scalar This value loses its tag.

hash_keeps_tag: !hash_tag
  keeps_tag: *anchor_keeps_tag
  loses_tag: *anchor_loses_tag
  gains_tag: *anchor_gains_tag
  none_tag: *anchor_none_tag
  tag_none: Neither gains nor loses its tag.
  tag_keep: !tagged_scalar Keeps its tag.
  tag_adds: This value gains a tag.
  tag_drops: !tagged_scalar This value loses its tag.

array_loses_tag: !array_tag
  - *anchor_keeps_tag
  - *anchor_loses_tag
  - *anchor_gains_tag
  - *anchor_none_tag
  - Neither gains nor loses its tag.
  - !tagged_scalar Keeps its tag.
  - This value gains a tag.
  - !tagged_scalar This value loses its tag.

array_gains_tag:
  - *anchor_keeps_tag
  - *anchor_loses_tag
  - *anchor_gains_tag
  - *anchor_none_tag
  - Neither gains nor loses its tag.
  - !tagged_scalar Keeps its tag.
  - This value gains a tag.
  - !tagged_scalar This value loses its tag.

array_none_tag:
  - *anchor_keeps_tag
  - *anchor_loses_tag
  - *anchor_gains_tag
  - *anchor_none_tag
  - Neither gains nor loses its tag.
  - !tagged_scalar Keeps its tag.
  - This value gains a tag.
  - !tagged_scalar This value loses its tag.

array_keeps_tag: !array_tag
  - *anchor_keeps_tag
  - *anchor_loses_tag
  - *anchor_gains_tag
  - *anchor_none_tag
  - Neither gains nor loses its tag.
  - !tagged_scalar Keeps its tag.
  - This value gains a tag.
  - !tagged_scalar This value loses its tag.
""")
        rhs_content = """---
aliases:
  - &anchor_keeps_tag !tagged_scalar This anchored scalar keeps its tag.
  - &anchor_loses_tag This anchored scalar loses its tag.
  - &anchor_gains_tag !tagged_scalar This anchored scalar gains a tag.
  - &anchor_none_tag An anchored scalar with no tag.

hash_loses_tag:
  keeps_tag: *anchor_keeps_tag
  loses_tag: *anchor_loses_tag
  gains_tag: *anchor_gains_tag
  none_tag: *anchor_none_tag
  tag_none: Neither gains nor loses its tag.
  tag_keep: !tagged_scalar Keeps its tag.
  tag_adds: !tagged_scalar This value gains a tag.
  tag_drops: This value loses its tag.

hash_gains_tag: !hash_tag
  keeps_tag: *anchor_keeps_tag
  loses_tag: *anchor_loses_tag
  gains_tag: *anchor_gains_tag
  none_tag: *anchor_none_tag
  tag_none: Neither gains nor loses its tag.
  tag_keep: !tagged_scalar Keeps its tag.
  tag_adds: !tagged_scalar This value gains a tag.
  tag_drops: This value loses its tag.

hash_none_tag:
  keeps_tag: *anchor_keeps_tag
  loses_tag: *anchor_loses_tag
  gains_tag: *anchor_gains_tag
  none_tag: *anchor_none_tag
  tag_none: Neither gains nor loses its tag.
  tag_keep: !tagged_scalar Keeps its tag.
  tag_adds: !tagged_scalar This value gains a tag.
  tag_drops: This value loses its tag.

hash_keeps_tag: !hash_tag
  keeps_tag: *anchor_keeps_tag
  loses_tag: *anchor_loses_tag
  gains_tag: *anchor_gains_tag
  none_tag: *anchor_none_tag
  tag_none: Neither gains nor loses its tag.
  tag_keep: !tagged_scalar Keeps its tag.
  tag_adds: !tagged_scalar This value gains a tag.
  tag_drops: This value loses its tag.

array_loses_tag:
  - *anchor_keeps_tag
  - *anchor_loses_tag
  - *anchor_gains_tag
  - *anchor_none_tag
  - Neither gains nor loses its tag.
  - !tagged_scalar Keeps its tag.
  - !tagged_scalar This value gains a tag.
  - This value loses its tag.

array_gains_tag: !array_tag
  - *anchor_keeps_tag
  - *anchor_loses_tag
  - *anchor_gains_tag
  - *anchor_none_tag
  - Neither gains nor loses its tag.
  - !tagged_scalar Keeps its tag.
  - !tagged_scalar This value gains a tag.
  - This value loses its tag.

array_none_tag:
  - *anchor_keeps_tag
  - *anchor_loses_tag
  - *anchor_gains_tag
  - *anchor_none_tag
  - Neither gains nor loses its tag.
  - !tagged_scalar Keeps its tag.
  - !tagged_scalar This value gains a tag.
  - This value loses its tag.

array_keeps_tag: !array_tag
  - *anchor_keeps_tag
  - *anchor_loses_tag
  - *anchor_gains_tag
  - *anchor_none_tag
  - Neither gains nor loses its tag.
  - !tagged_scalar Keeps its tag.
  - !tagged_scalar This value gains a tag.
  - This value loses its tag.
"""
        merged_yaml_content = """---
aliases:
  - &anchor_keeps_tag !tagged_scalar This anchored scalar keeps its tag.
  - &anchor_loses_tag This anchored scalar loses its tag.
  - &anchor_gains_tag !tagged_scalar This anchored scalar gains a tag.
  - &anchor_none_tag An anchored scalar with no tag.
hash_loses_tag:
  keeps_tag: *anchor_keeps_tag
  loses_tag: *anchor_loses_tag
  gains_tag: *anchor_gains_tag
  none_tag: *anchor_none_tag
  tag_none: Neither gains nor loses its tag.
  tag_keep: !tagged_scalar Keeps its tag.
  tag_adds: !tagged_scalar This value gains a tag.
  tag_drops: This value loses its tag.
hash_gains_tag: !hash_tag
  keeps_tag: *anchor_keeps_tag
  loses_tag: *anchor_loses_tag
  gains_tag: *anchor_gains_tag
  none_tag: *anchor_none_tag
  tag_none: Neither gains nor loses its tag.
  tag_keep: !tagged_scalar Keeps its tag.
  tag_adds: !tagged_scalar This value gains a tag.
  tag_drops: This value loses its tag.
hash_none_tag:
  keeps_tag: *anchor_keeps_tag
  loses_tag: *anchor_loses_tag
  gains_tag: *anchor_gains_tag
  none_tag: *anchor_none_tag
  tag_none: Neither gains nor loses its tag.
  tag_keep: !tagged_scalar Keeps its tag.
  tag_adds: !tagged_scalar This value gains a tag.
  tag_drops: This value loses its tag.
hash_keeps_tag: !hash_tag
  keeps_tag: *anchor_keeps_tag
  loses_tag: *anchor_loses_tag
  gains_tag: *anchor_gains_tag
  none_tag: *anchor_none_tag
  tag_none: Neither gains nor loses its tag.
  tag_keep: !tagged_scalar Keeps its tag.
  tag_adds: !tagged_scalar This value gains a tag.
  tag_drops: This value loses its tag.
array_loses_tag:
  - *anchor_keeps_tag
  - *anchor_loses_tag
  - *anchor_gains_tag
  - *anchor_none_tag
  - Neither gains nor loses its tag.
  - !tagged_scalar Keeps its tag.
  - !tagged_scalar This value gains a tag.
  - This value loses its tag.
array_gains_tag: !array_tag
  - *anchor_keeps_tag
  - *anchor_loses_tag
  - *anchor_gains_tag
  - *anchor_none_tag
  - Neither gains nor loses its tag.
  - !tagged_scalar Keeps its tag.
  - !tagged_scalar This value gains a tag.
  - This value loses its tag.
array_none_tag:
  - *anchor_keeps_tag
  - *anchor_loses_tag
  - *anchor_gains_tag
  - *anchor_none_tag
  - Neither gains nor loses its tag.
  - !tagged_scalar Keeps its tag.
  - !tagged_scalar This value gains a tag.
  - This value loses its tag.
array_keeps_tag: !array_tag
  - *anchor_keeps_tag
  - *anchor_loses_tag
  - *anchor_gains_tag
  - *anchor_none_tag
  - Neither gains nor loses its tag.
  - !tagged_scalar Keeps its tag.
  - !tagged_scalar This value gains a tag.
  - This value loses its tag.
"""

        result = subprocess.run(
            [self.command
            , "--anchors=right"
            , "--arrays=unique"
            , lhs_file]
            , stdout=subprocess.PIPE
            , input=rhs_content
            , universal_newlines=True
        )

        # DEBUG
        # print("Expected:")
        # print(merged_yaml_content)
        # print("Got:")
        # print(result.stdout)

        assert 0 == result.returncode, result.stderr
        assert merged_yaml_content == result.stdout

    def test_tagged_key_merging(
        self, script_runner, tmp_path_factory
    ):
        import subprocess

        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &keeps_tag !tagged keeps
  - &loses_tag !tagged loses
  - &gains_tag gains
  - &never_tag never

*keeps_tag : !hash_keeps
  *keeps_tag : *keeps_tag
  *loses_tag : *loses_tag
  *gains_tag : *gains_tag
  *never_tag : *never_tag

*loses_tag : !hash_loses
  *keeps_tag : *keeps_tag
  *loses_tag : *loses_tag
  *gains_tag : *gains_tag
  *never_tag : *never_tag

*gains_tag :
  *keeps_tag : *keeps_tag
  *loses_tag : *loses_tag
  *gains_tag : *gains_tag
  *never_tag : *never_tag

*never_tag :
  *keeps_tag : *keeps_tag
  *loses_tag : *loses_tag
  *gains_tag : *gains_tag
  *never_tag : *never_tag
""")
        rhs_content = """---
aliases:
  - &keeps_tag !tagged keeps
  - &loses_tag loses
  - &gains_tag !tagged gains
  - &never_tag never

*keeps_tag : !hash_keeps
  *keeps_tag : *keeps_tag
  *loses_tag : *loses_tag
  *gains_tag : *gains_tag
  *never_tag : *never_tag

*loses_tag :
  *keeps_tag : *keeps_tag
  *loses_tag : *loses_tag
  *gains_tag : *gains_tag
  *never_tag : *never_tag

*gains_tag : !hash_loses
  *keeps_tag : *keeps_tag
  *loses_tag : *loses_tag
  *gains_tag : *gains_tag
  *never_tag : *never_tag

*never_tag :
  *keeps_tag : *keeps_tag
  *loses_tag : *loses_tag
  *gains_tag : *gains_tag
  *never_tag : *never_tag
"""
        merged_yaml_content = """---
aliases:
  - &keeps_tag !tagged keeps
  - &loses_tag loses
  - &gains_tag !tagged gains
  - &never_tag never
*keeps_tag : !hash_keeps
  *keeps_tag : *keeps_tag
  *loses_tag : *loses_tag
  *gains_tag : *gains_tag
  *never_tag : *never_tag
*loses_tag :
  *keeps_tag : *keeps_tag
  *loses_tag : *loses_tag
  *gains_tag : *gains_tag
  *never_tag : *never_tag
*gains_tag : !hash_loses
  *keeps_tag : *keeps_tag
  *loses_tag : *loses_tag
  *gains_tag : *gains_tag
  *never_tag : *never_tag
*never_tag :
  *keeps_tag : *keeps_tag
  *loses_tag : *loses_tag
  *gains_tag : *gains_tag
  *never_tag : *never_tag
"""

        result = subprocess.run(
            [self.command
            , "--anchors=right"
            , "--arrays=unique"
            , lhs_file]
            , stdout=subprocess.PIPE
            , input=rhs_content
            , universal_newlines=True
        )

        # DEBUG
        # print("Expected:")
        # print(merged_yaml_content)
        # print("Got:")
        # print(result.stdout)

        assert 0 == result.returncode, result.stderr
        assert merged_yaml_content == result.stdout

    def test_tagged_aoh_merging(
        self, script_runner, tmp_path_factory
    ):
        import subprocess

        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
ports:
  - !public_record
    id: !privileged 7
    name: echo
    tcp: true
    udp: true
  - id: 15
    name: netstat
    tcp: true
    udp: false
  - !public_record
    id: !privileged 80
    name: http
    tcp: true
    udp: true
  - id: 113
    name: ident
    tcp: true
    udp: false
  - !inferred_record
    id: !unprivileged 1666
    name: perforce
    tcp: true
    udp: false
  - id: 1812
    name: radius
    tcp: true
    udp: true
  - !inferred_record
    id: !unprivileged 1813
    name: radius-acct
    tcp: true
    udp: true
  - id: 2083
    name: radsec
    tcp: true
    udp: true
""")
        rhs_content = """---
ports:
  - !public_record
    id: !privileged 7
    name: echo
    tcp: true
    udp: true
  - id: 15
    name: netstat
    tcp: true
    udp: false
  - id: 80
    name: http
    tcp: true
    udp: true
  - !public_record
    id: !privileged 113
    name: ident
    tcp: true
    udp: false
  - !inferred_record
    id: !unprivileged 1666
    name: perforce
    tcp: true
    udp: false
  - id: 1812
    name: radius
    tcp: true
    udp: true
  - id: 1813
    name: radius-acct
    tcp: true
    udp: true
  - !inferred_record
    id: !unprivileged 2083
    name: radsec
    tcp: true
    udp: true
"""
        merged_yaml_content = """---
ports:
  - !public_record
    id: !privileged 7
    name: echo
    tcp: true
    udp: true
  - id: 15
    name: netstat
    tcp: true
    udp: false
  - id: 80
    name: http
    tcp: true
    udp: true
  - !public_record
    id: !privileged 113
    name: ident
    tcp: true
    udp: false
  - !inferred_record
    id: !unprivileged 1666
    name: perforce
    tcp: true
    udp: false
  - id: 1812
    name: radius
    tcp: true
    udp: true
  - id: 1813
    name: radius-acct
    tcp: true
    udp: true
  - !inferred_record
    id: !unprivileged 2083
    name: radsec
    tcp: true
    udp: true
"""

        result = subprocess.run(
            [self.command
            , "--aoh=deep"
            , lhs_file]
            , stdout=subprocess.PIPE
            , input=rhs_content
            , universal_newlines=True
        )

        # DEBUG
        # print("Expected:")
        # print(merged_yaml_content)
        # print("Got:")
        # print(result.stdout)

        assert 0 == result.returncode, result.stderr
        assert merged_yaml_content == result.stdout
