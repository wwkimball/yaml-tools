import pytest

from types import SimpleNamespace
from distutils.util import strtobool

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedSeq, CommentedMap
from ruamel.yaml.scalarstring import PlainScalarString
from ruamel.yaml.scalarbool import ScalarBoolean
from ruamel.yaml.scalarfloat import ScalarFloat
from ruamel.yaml.scalarint import ScalarInt

from yamlpath import YAMLPath, Parser
from yamlpath.exceptions import YAMLPathException
from yamlpath.enums import (
    YAMLValueFormats,
    PathSegmentTypes,
    PathSearchMethods,
    PathSeperators,
)
from yamlpath.wrappers import ConsolePrinter


# Define a set of single-match inputs that are used for multiple tests
single_match_tests = [
    ("aliases[&test_scalarstring]", "This is a scalar string."),
    ("/aliases[&test_foldedstring]", "This is a folded multi-line string."),
    ("aliases[&test_literalstring]", "This is a\nliteral multi-line\nstring."),
    ("/top_scalar", "value"),
    ("top_alias", "This is a scalar string."),
    ("/top_array_anchor[0]", "This is a scalar string."),
    ("/top_array_anchor/0", "This is a scalar string."),
    ("top_array_anchor[1]", "An original value"),
    ("top_array_anchor.1", "An original value"),
    ("/top_array_anchor[2]", "This is a folded multi-line string."),
    ("/top_array_anchor/2", "This is a folded multi-line string."),
    ("top_array_anchor[3]", "Another original value"),
    ("top_array_anchor.3", "Another original value"),
    ("/&topArrayAnchor[0]", "This is a scalar string."),
    ("/&topArrayAnchor/0", "This is a scalar string."),
    ("&topArrayAnchor[1]", "An original value"),
    ("&topArrayAnchor.1", "An original value"),
    ("/&topArrayAnchor[2]", "This is a folded multi-line string."),
    ("/&topArrayAnchor/2", "This is a folded multi-line string."),
    ("&topArrayAnchor[3]", "Another original value"),
    ("&topArrayAnchor.3", "Another original value"),
    ("/sub_hash_anchor/child1/attr_tst", "child 1"),
    ("sub_hash_anchor.child1.attr_val", 100),
    ("/sub_hash_anchor/child2/attr_tst", "child 2"),
    ("sub_hash_anchor.child2.attr_val", 200),
    ("/sub_hash_anchor/child3/attr_tst", "child 3"),
    ("sub_hash_anchor.child3.attr_val", 300),
    ("/sub_hash_anchor/childN/attr_tst", "child N"),
    ("sub_hash_anchor.childN.attr_val", 999),
    ("/&subHashAnchor/child1/attr_tst", "child 1"),
    ("&subHashAnchor.child1.attr_val", 100),
    ("/&subHashAnchor/child2/attr_tst", "child 2"),
    ("&subHashAnchor.child2.attr_val", 200),
    ("/&subHashAnchor/child3/attr_tst", "child 3"),
    ("&subHashAnchor.child3.attr_val", 300),
    ("/&subHashAnchor/childN/attr_tst", "child N"),
    ("&subHashAnchor.childN.attr_val", 999),
    ("/top_hash_anchor/key1", "value 1"),
    ("top_hash_anchor.key2", "value 2"),
    ("/top_hash_anchor/key3", "value 3"),
    ("top_hash_anchor.key_complex.child1.attr_tst", "child 1"),
    ("/top_hash_anchor/key_complex/child1/attr_val", 100),
    ("top_hash_anchor.key_complex.child2.attr_tst", "child 2"),
    ("/top_hash_anchor/key_complex/child2/attr_val", 200),
    ("top_hash_anchor.key_complex.child3.attr_tst", "child 3"),
    ("/top_hash_anchor/key_complex/child3/attr_val", 300),
    ("/top_hash_anchor/key_complex/childN/attr_tst", "child N"),
    ("top_hash_anchor.key_complex.childN.attr_val", 999),
    ("&topHashAnchor.key1", "value 1"),
    ("/&topHashAnchor/key2", "value 2"),
    ("&topHashAnchor.key3", "value 3"),
    ("/&topHashAnchor/key_complex/child1/attr_tst", "child 1"),
    ("&topHashAnchor.key_complex.child1.attr_val", 100),
    ("&topHashAnchor.key_complex.child2.attr_tst", "child 2"),
    ("/&topHashAnchor/key_complex/child2/attr_val", 200),
    ("&topHashAnchor.key_complex.child3.attr_tst", "child 3"),
    ("/&topHashAnchor/key_complex/child3/attr_val", 300),
    ("/&topHashAnchor/key_complex/childN/attr_tst", "child N"),
    ("&topHashAnchor.key_complex.childN.attr_val", 999),
    ("namespaced::hash.with_array[0]", "one"),
    ("/namespaced::hash/with_array[1]", "two"),
    ("namespaced::hash.with_array[2]", "three"),
    ("namespaced::hash.with_array_of_hashes[0].id", 1),
    ("/namespaced::hash/with_array_of_hashes[0]/name", "ichi"),
    ("/namespaced::hash/with_array_of_hashes[1]/id", 2),
    ("namespaced::hash.with_array_of_hashes[1].name", "ni"),
    ("/namespaced::hash/with_array_of_hashes[2]/id", 3),
    ("namespaced::hash.with_array_of_hashes[2].name", "san"),
    ("/namespaced::hash/with_array_alias[0]", "This is a scalar string."),
    ("namespaced::hash.with_array_alias[1]", "An original value"),
    ("/namespaced::hash/with_array_alias[2]", "This is a folded multi-line string."),
    ("namespaced::hash.with_array_alias[3]", "Another original value"),
    ("/namespaced::hash/with_hash_alias/key1", "value 1"),
    ("namespaced::hash.with_hash_alias.key2", "value 2"),
    ("/namespaced::hash/with_hash_alias/key3", "value 3.2"),
    ("namespaced::hash.with_hash_alias.key4", "value 4.0"),
    ("/namespaced::hash/with_hash_alias/key_complex/child1/attr_tst", "child 1"),
    ("namespaced::hash.with_hash_alias.key_complex.child1.attr_val", 100),
    ("namespaced::hash.with_hash_alias.key_complex.child2.attr_tst", "child 2"),
    ("/namespaced::hash/with_hash_alias/key_complex/child2/attr_val", 200),
    ("namespaced::hash.with_hash_alias.key_complex.child3.attr_tst", "child 3"),
    ("/namespaced::hash/with_hash_alias/key_complex/child3/attr_val", 300),
    ("/namespaced::hash/with_hash_alias/key_complex/child4/attr_tst", "child 4"),
    ("namespaced::hash.with_hash_alias.key_complex.child4.attr_val", 400),
    ("/namespaced::hash/with_hash_alias/key_complex/child5/attr_tst", "child 5"),
    ("namespaced::hash.with_hash_alias.key_complex.child5.attr_val", 500),
    ("/namespaced::hash/with_hash_alias/key_complex/childN/attr_tst", "child N2"),
    ("namespaced::hash.with_hash_alias.key_complex.childN.attr_val", 0),
    (r"namespaced::hash.and\.with\.dotted\.child.that", "has it's own"),
    (r"/namespaced::hash/and.with.dotted.child/child", "nodes"),
    ("namespaced::hash.with_array_of_hashes[id=1].name", "ichi"),
    ("/namespaced::hash/with_array_of_hashes[name=ichi]/id", 1),
    ("namespaced::hash.with_array_of_hashes[name='ichi'].id", 1),
    ("/namespaced::hash/with_array_of_hashes[id=2]/name", "ni"),
    ("namespaced::hash.with_array_of_hashes[name=ni].id", 2),
    ("/namespaced::hash/with_array_of_hashes[name='ni']/id", 2),
    ("/namespaced::hash/with_array_of_hashes[id=3]/name", "san"),
    ("namespaced::hash.with_array_of_hashes[name=san].id", 3),
    ("namespaced::hash.with_array_of_hashes[name='san'].id", 3),
    ("/namespaced::hash/with_array_of_hashes[name^ich]/id", 1),
    ("namespaced::hash.with_array_of_hashes[name$n].id", 3),
    (r"namespaced::hash.with_array_of_hashes[name%a].id", 3),
    ("namespaced::hash.with_array_of_hashes[id<2].name", "ichi"),
    ("/namespaced::hash/with_array_of_hashes[id>2]/name", "san"),
    ("/namespaced::hash/with_array_of_hashes[id<=1]/name", "ichi"),
    ("namespaced::hash.with_array_of_hashes[id>=3].name", "san"),
    (r"namespaced::hash.with_array_of_hashes[name!%i].id", 3),
    (r"/[.^top_][.^key][.^child][attr_tst=child\ 2]", "child 2"),
    (r"complex.hash_of_hashes[.=~/^child\d+/].children[third=~/^j[^u]\s\w+$/]", "ji ni"),
    (r"/complex/hash_of_hashes[.=~/^child[0-9]+/]/children[third=~/^j[^u] \w+$/]", "ji ni"),
    (r"complex.hash_of_hashes[.=~_^child\d+_].children[third=~#^j[^u] \w+$#]", "ji ni"),
    (r"/complex/hash_of_hashes[ . =~ !^child\d+! ]/children[ third =~ a^j[^u] \w+$a ]", "ji ni"),
    (r"complex.hash_of_hashes[.=~ -^child\d+-].children[third =~ $^j[^u] \w+$]", "ji ni"),
    ("namespaced::hash.with_array[1:1]", "two"),
    ("/namespaced::hash/with_array[1:1]", "two"),
]

# Define a set of multiple-match inputs that are used for multiple tests
multi_matche_tests = [
    ("namespaced::hash.with_array_of_hashes[id<3].name", ["ichi", "ni"]),
    ("namespaced::hash.with_array_of_hashes[id<3].id", [1, 2]),
    ("namespaced::hash.with_array_of_hashes[id<=3].name", ["ichi", "ni", "san"]),
    ("namespaced::hash.with_array_of_hashes[id<=3].id", [1, 2, 3]),
    ("namespaced::hash.with_array_of_hashes[id>1].id", [2, 3]),
    ("namespaced::hash.with_array_of_hashes[id>1].name", ["ni", "san"]),
    ("namespaced::hash.with_array_of_hashes[id>=2].id", [2, 3]),
    ("namespaced::hash.with_array_of_hashes[id>=2].name", ["ni", "san"]),
    ("namespaced::hash.with_array_of_hashes[!id>=2].name", ["ichi"]),
    ("namespaced::hash.with_array_of_hashes[!id>=2].id", [1]),
    ("namespaced::hash.with_array_of_hashes[name>na].name", ["ni", "san"]),
    ("namespaced::hash.with_array_of_hashes[name>na].name", ["ni", "san"]),
    ("namespaced::hash.with_array_of_hashes[name>=ni].name", ["ni", "san"]),
    ("namespaced::hash.with_array_of_hashes[name<san].name", ["ichi", "ni"]),
    ("namespaced::hash.with_array_of_hashes[name<=ni].name", ["ichi", "ni"]),
    ("complex.hash_of_hashes[.^child].children.first", ["ichi", "shi", "shichi", "ju"]),
    (r"complex.hash_of_hashes[.^child].children[first%ichi]", ["ichi", "shichi"]),
    (r"&topArrayAnchor[.%original]", ["An original value", "Another original value"]),
    ("namespaced::hash.with_array[0:2]", [["one", "two"]]),
    ("/namespaced::hash/with_array[0:2]", [["one", "two"]]),
    ("&topHashAnchor[key1:key2]", ["value 1", "value 2"]),
    ("/&topHashAnchor[key1:key2]", ["value 1", "value 2"]),
    ("namespaced::hash.with_array_of_hashes[0:2].id", [1, 2]),
    ("/namespaced::hash/with_array_of_hashes[0:2]/id", [1, 2]),
]

@pytest.fixture
def quiet_logger():
    args = SimpleNamespace(verbose=False, quiet=True, debug=False)
    return ConsolePrinter(args)

@pytest.fixture
def yamlpath(quiet_logger):
    """Returns a YAMLPath with a quiet logger."""
    return YAMLPath(quiet_logger)

@pytest.fixture
def yamldata():
    data = """---
aliases:
  - &test_scalarstring This is a scalar string.
  - &test_foldedstring >-
    This is a
    folded multi-line
    string.
  - &test_literalstring |-
    This is a
    literal multi-line
    string.

top_scalar:  value
top_alias: *test_scalarstring
top_array_anchor: &topArrayAnchor
  - *test_scalarstring
  - An original value
  - *test_foldedstring
  - Another original value

sub_hash_anchor: &subHashAnchor
  child1:
    attr_tst: child 1
    attr_val: 100
  child2:
    attr_tst: child 2
    attr_val: 200
  child3:
    attr_tst: child 3
    attr_val: 300
  childN:
    attr_tst: child N
    attr_val: 999
top_hash_anchor: &topHashAnchor
  key1: value 1
  key2: value 2
  key3: value 3
  key_complex:
    <<: *subHashAnchor

namespaced::hash:
  with_array:
    - one
    - two
    - three
  with_array_of_hashes:
    - id: 1
      name: ichi
      ref: 1.4142135623
    - id: 2
      name: ni
      ref: 2.7182818284
    - id: 3
      name: san
      ref: 3.1415926535
  with_array_alias: *topArrayAnchor
  with_hash_alias:
    <<: *topHashAnchor
    key3: value 3.2
    key4: value 4.0
    key_complex:
      <<: *subHashAnchor
      child4:
        attr_tst: child 4
        attr_val: 400
      child5:
        attr_tst: child 5
        attr_val: 500
      childN:
        attr_tst: child N2
        attr_val: 0
  'and.with.dotted.child':
    that: has it's own
    child: nodes

complex:
  array_of_hashes:
    - id: 1
      key: child1
      name: one
      children:
        first: ichi
        second: ni
        third: san
    - id: 2
      key: child2
      name: two
      children:
        first: shi
        second: go
        third: roku
    - id: 3
      key: child3
      name: three
      children:
        first: shichi
        second: hachi
        third: ku
    - id: 4
      key: child4
      name: four
      children:
        first: ju
        second: ju ichi
        third: ji ni     # Deliberate typo for testing (should be "ju ni")
  hash_of_hashes:
    child1:
      id: 1
      name: one
      children:
        first: ichi
        second: ni
        third: san
    child2:
      id: 2
      name: two
      children:
        first: shi
        second: go
        third: roku
    child3:
      id: 3
      name: three
      children:
        first: shichi
        second: hachi
        third: ku
    child4:
      id: 4
      name: four
      children:
        first: ju
        second: ju ichi
        third: ji ni
"""
    yaml = YAML()
    return yaml.load(data)

@pytest.mark.parametrize("mustexist", [
    (True),
    (False),
])
def test_get_none_path_to_nodes_public(yamlpath, yamldata, mustexist):
    for node in yamlpath.get_nodes(yamldata, None, mustexist=mustexist):
        assert node == None

@pytest.mark.parametrize("mustexist", [
    (True),
    (False),
])
def test_get_none_data_to_nodes_public(yamlpath, yamldata, mustexist):
    for node in yamlpath.get_nodes(None, "top_scalar", mustexist=mustexist):
        assert node == None

def test_get_none_data_to_nodes_private(yamlpath, yamldata):
    for node in yamlpath._get_nodes(None, "top_scalar"):
        assert node == None

def test_get_none_path_to_nodes_private(yamlpath, yamldata):
    for node in yamlpath._get_nodes(yamldata, None):
        assert node == None

def test_ensure_none_path(yamlpath, yamldata):
    for node in yamlpath._ensure_path(yamldata, None):
        assert node == None

def test_empty_set_nodes(yamlpath, yamldata):
    # Should do nothing and not raise any exceptions
    yamlpath.set_value(None, "aliases[&dnf]", "New Value")
    yamlpath.set_value(yamldata, None, "New Value")

@pytest.mark.parametrize("search,compare", single_match_tests)
def test_happy_singular_get_leaf_nodes_opt(yamlpath, yamldata, search, compare):
    for node in yamlpath.get_nodes(yamldata, search):
        assert node == compare

@pytest.mark.parametrize("search,compare", single_match_tests)
def test_happy_singular_get_leaf_nodes_req(yamlpath, yamldata, search, compare):
    for node in yamlpath.get_nodes(yamldata, search, mustexist=True):
        assert node == compare

@pytest.mark.parametrize("search,compare", multi_matche_tests)
def test_happy_multiple_get_nodes_opt(yamlpath, yamldata, search, compare):
    matches = []
    for node in yamlpath.get_nodes(yamldata, search):
        matches.append(node)
    assert matches == compare

@pytest.mark.parametrize("search,compare", multi_matche_tests)
def test_happy_multiple_get_nodes_req(yamlpath, yamldata, search, compare):
    matches = []
    for node in yamlpath.get_nodes(yamldata, search, mustexist=True):
        matches.append(node)
    assert matches == compare

@pytest.mark.parametrize("search,compare", [
    ("&doesNotExist", "No such top-level Anchor!"),
    ("aliases[&doesNotExist]", "This listed Anchor does not exist!"),
    ("top_fake_scalar", "No such value."),
    ("top_array_anchor[4]", "No such index."),
    ("top_array_anchor[4F]", "Invalid index."),
    ("namespaced::hash.with_array_of_hashes[id=4F].id", "Invalid index"),
    ("namespaced::hash.with_array_of_hashes[id>4F].id", "Invalid index"),
    ("namespaced::hash.with_array_of_hashes[id>=4F].id", "Invalid index"),
    ("namespaced::hash.with_array_of_hashes[id<4F].id", "Invalid index"),
    ("namespaced::hash.with_array_of_hashes[id<=4F].id", "Invalid index"),
    ("namespaced::hash.with_array_of_hashes[ref=1.41F].id", "Invalid index"),
    ("namespaced::hash.with_array_of_hashes[ref>1.41F].id", "Invalid index"),
    ("namespaced::hash.with_array_of_hashes[ref>=1.41F].id", "Invalid index"),
    ("namespaced::hash.with_array_of_hashes[ref<1.41F].id", "Invalid index"),
    ("namespaced::hash.with_array_of_hashes[ref<=1.41F].id", "Invalid index"),
    ("namespaced::hash.with_array[1:4F]", "borked"),
    ("/namespaced::hash/with_array[4F:1]", "borken"),
])
def test_unhappy_singular_get_leaf_nodes(yamlpath, yamldata, search, compare):
    with pytest.raises(YAMLPathException):
        for node in yamlpath.get_nodes(yamldata, search, mustexist=True):
            node == compare

@pytest.mark.parametrize("search,compare", [
    ("new_top_scalarstring", "String data"),
    ("new_top_scalarint", 10),
    ("new_top_scalarfloat", 10.01),
    ("new_top_scalarbool", True),
    ("aliases[&doesNotExist]", "Sample data"),
    ("new_top_array[7]", "Repeated seven times data"),
    ("new_top_hash.with.many.'levels.of.sub'.keys", "Including dotted sub-keys"),
    ("new_top_hash.with.'an.original'.new_array[3]", "Including dotted sub-keys and three new elments"),
])
def test_happy_adding_nodes(yamlpath, yamldata, search, compare):
    for node in yamlpath.get_nodes(yamldata, search, mustexist=False, default_value=compare):
        assert node == compare

@pytest.mark.parametrize("search,compare", [
    ("top_scalar.impossible.hash.reference", "Can't convert an Scalar into a Hash"),
    ("aliases.cannot.do.this", "Can't convert an Array into a Hash"),
    ("sub_hash_anchor[4]", "Can't convert a Hash into an Array"),
])
def test_unhappy_adding_nodes(yamlpath, yamldata, search, compare):
    with pytest.raises(YAMLPathException):
        for node in yamlpath.get_nodes(yamldata, search, mustexist=False, default_value=compare):
            node == compare

def test_clone_raw_node(yamlpath, yamldata):
    test_value = "Some string."
    assert test_value == yamlpath.clone_node(test_value)


def test_clone_data_node(yamlpath, yamldata):
    for node in yamlpath.get_nodes(yamldata, "aliases[0]"):
        assert node == yamlpath.clone_node(node)

@pytest.mark.parametrize("search,compare,vformat,mexist", [
    ("aliases[&test_scalarstring]", "A whole new BARE value.", YAMLValueFormats.BARE, True),
    ("aliases[&test_scalarstring]", "A whole new DQUOTE value.", YAMLValueFormats.DQUOTE, True),
    ("aliases[&test_scalarstring]", "A whole new SQUOTE value.", YAMLValueFormats.SQUOTE, True),
    ("aliases[&test_scalarstring]", "A whole new FOLDED value.", YAMLValueFormats.FOLDED, True),
    ("aliases[&test_scalarstring]", "A whole new LITERAL value.", YAMLValueFormats.LITERAL, True),
    ("aliases[&new_scalarfloat]", 10.01, YAMLValueFormats.FLOAT, False),
    ("aliases[&new_scalarint]", 42, YAMLValueFormats.INT, False),
    ("aliases[&test_scalarstring]", "A whole new bare value.", "bare", True),
    ("aliases[&test_scalarstring]", "A whole new dquote value.", "dquote", True),
    ("aliases[&test_scalarstring]", "A whole new squote value.", "squote", True),
    ("aliases[&test_scalarstring]", "A whole new folded value.", "folded", True),
    ("aliases[&test_scalarstring]", "A whole new literal value.", "literal", True),
    ("aliases[&new_scalarfloat]", 1.1, "float", False),
    ("aliases[&new_scalarint]", 24, "int", False),
    ("aliases[&new_scalarstring]", "Did not previously exist.", YAMLValueFormats.BARE, False),
])
def test_happy_set_value(yamlpath, yamldata, search, compare, vformat, mexist):
    yamlpath.set_value(yamldata, search, compare, value_format=vformat, mustexist=mexist)
    for node in yamlpath.get_nodes(yamldata, search, mustexist=True):
        assert node == compare

@pytest.mark.parametrize("search,compare,vformat,mexist", [
    ("aliases[&new_scalarbool]", True, YAMLValueFormats.BOOLEAN, False),
    ("aliases[&new_scalarbool]", "true", YAMLValueFormats.BOOLEAN, False),
    ("aliases[&new_scalarbool]", False, "boolean", False),
    ("aliases[&new_scalarbool]", "false", "boolean", False),
])
def test_happy_set_bool_value(yamlpath, yamldata, search, compare, vformat, mexist):
    yamlpath.set_value(yamldata, search, compare, value_format=vformat, mustexist=mexist)
    checkval = compare
    if isinstance(compare, str):
        checkval = strtobool(compare)
    for node in yamlpath.get_nodes(yamldata, search, mustexist=True):
        assert node == checkval

@pytest.mark.parametrize("search,compare,vformat,mexist", [
    ("aliases[&new_scalarstring]", "Did not previously exist.", YAMLValueFormats.BARE, True),
])
def test_unhappy_set_value(yamlpath, yamldata, search, compare, vformat, mexist):
    with pytest.raises(YAMLPathException):
        yamlpath.set_value(yamldata, search, compare, value_format=vformat, mustexist=mexist)

@pytest.mark.parametrize("search,compare,vformat,mexist", [
    ("aliases[&new_scalarstring]", "Did not previously exist.", YAMLValueFormats.BARE, True),
])
def test_yamlpatherror_str(yamlpath, yamldata, search, compare, vformat, mexist):
    try:
        yamlpath.set_value(yamldata, search, compare, value_format=vformat, mustexist=mexist)
    except YAMLPathException as ex:
        assert str(ex)

def test_bad_value_format(yamlpath, yamldata):
    with pytest.raises(NameError):
        yamlpath.set_value(yamldata, "aliases[&test_scalarstring]", "Poorly formatted value.", value_format="no_such_format", mustexist=False)

@pytest.mark.parametrize("val,typ", [
    ([], CommentedSeq),
    ({}, CommentedMap),
    ("", PlainScalarString),
    (1, ScalarInt),
    (1.1, ScalarFloat),
    (True, ScalarBoolean),
    (SimpleNamespace(), SimpleNamespace),
])
def test_wrap_type(val, typ):
  assert isinstance(YAMLPath.wrap_type(val), typ)

def test_default_for_child_none(yamlpath):
  assert isinstance(yamlpath.default_for_child(None, ""), str)

@pytest.mark.parametrize("path,typ", [
  ([(True, False)], ScalarBoolean),
  ([(str, "")], PlainScalarString),
  ([(int, 1)], ScalarInt),
  ([(float, 1.1)], ScalarFloat),
])
def test_default_for_child(yamlpath, path, typ):
  assert isinstance(yamlpath.default_for_child(path, path[0][1]), typ)

def test_notimplementeds(yamlpath, yamldata):
  with pytest.raises(NotImplementedError):
    yamlpath.set_value(yamldata, "namespaced::hash[&newAnchor]", "New Value")

def test_scalar_search(yamlpath, yamldata):
  for node in yamlpath._search(yamldata["top_scalar"], [True, PathSearchMethods.EQUALS, ".", "top_scalar"]):
    assert node is not None

def test_nonexistant_path_search_method(yamlpath, yamldata):
  from enum import Enum
  from yamlpath.enums import PathSearchMethods
  names = [m.name for m in PathSearchMethods] + ['DNF']
  PathSearchMethods = Enum('PathSearchMethods', names)

  with pytest.raises(NotImplementedError):
    for _ in yamlpath._search(yamldata["top_scalar"], [True, PathSearchMethods.DNF, ".", "top_scalar"]):
      pass

def test_nonexistant_path_search_method_operator():
  from yamlpath.enums import PathSearchMethods
  with pytest.raises(NotImplementedError):
    _ = PathSearchMethods.to_operator("non-existant")

def test_nonexistant_path_segment_types(yamlpath, yamldata):
  from enum import Enum
  from yamlpath.enums import PathSegmentTypes
  names = [m.name for m in PathSegmentTypes] + ['DNF']
  PathSegmentTypes = Enum('PathSegmentTypes', names)

  with pytest.raises(NotImplementedError):
    for _ in yamlpath._get_elements_by_ref(yamldata, (PathSegmentTypes.DNF, ("", False, False))):
      pass

@pytest.mark.parametrize("sep,val", [
  ('.', PathSeperators.DOT),
  ('/', PathSeperators.FSLASH),
  ("DOT", PathSeperators.DOT),
  ("FSLASH", PathSeperators.FSLASH),
  (PathSeperators.DOT, PathSeperators.DOT),
  (PathSeperators.FSLASH, PathSeperators.FSLASH),
])
def test_seperators_from_str(sep, val):
  assert val == PathSeperators.from_str(sep)

def test_bad_separator_from_str():
  with pytest.raises(NameError):
    _ = PathSeperators.from_str("DNF")

def test_append_list_element_value_error(yamlpath):
  with pytest.raises(ValueError):
    yamlpath.append_list_element([], PathSearchMethods, "anchor")

def test_get_elements_by_bad_ref(yamlpath, yamldata):
  with pytest.raises(YAMLPathException):
    for _ in yamlpath._get_elements_by_ref(yamldata, (PathSegmentTypes.INDEX, ("bad_index[4F]", "4F", "4F"))):
      pass

def test_get_elements_by_none_refs(yamlpath, yamldata):
  tally = 0
  for _ in yamlpath._get_elements_by_ref(None, (PathSegmentTypes.INDEX, ("bad_index[4F]", "4F", "4F"))):
    tally += 1

  for _ in yamlpath._get_elements_by_ref(yamldata, None):
    tally += 1

  assert tally == 0

@pytest.mark.parametrize("newval,newform", [
  ("new value", YAMLValueFormats.LITERAL),
  (1.1, YAMLValueFormats.FLOAT),
])
def test_update_value(yamlpath, yamldata, newval, newform):
  yamlpath.update_node(yamldata, yamldata["top_scalar"], newval, newform)

@pytest.mark.parametrize("newval,newform", [
  ("4F", YAMLValueFormats.INT),
  ("4.F", YAMLValueFormats.FLOAT),
])
def test_bad_update_value(yamlpath, yamldata, newval, newform):
  with pytest.raises(ValueError):
    yamlpath.update_node(yamldata, yamldata["top_scalar"], newval, newform)

def test_yamlpath_exception():
  try:
    raise YAMLPathException("meh", "/some/path", "/some")
  except YAMLPathException as ex:
    _ = str(ex)

def test_premade_parser(quiet_logger):
  premade = Parser(quiet_logger)
  preload = YAMLPath(quiet_logger, parser=premade)
  assert preload.parser == premade
