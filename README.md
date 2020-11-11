# YAML Path and Command-Line Tools

[![Build Status](https://travis-ci.org/wwkimball/yamlpath.svg?branch=master)](https://travis-ci.org/wwkimball/yamlpath)
[![Python versions](https://img.shields.io/pypi/pyversions/yamlpath.svg)](https://pypi.org/project/yamlpath/)
[![PyPI version](https://badge.fury.io/py/yamlpath.svg)](https://pypi.org/project/yamlpath/)
[![Downloads](https://pepy.tech/badge/yamlpath)](https://pepy.tech/project/yamlpath)
[![Coverage Status](https://coveralls.io/repos/github/wwkimball/yamlpath/badge.svg?branch=master)](https://coveralls.io/github/wwkimball/yamlpath?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/6bcc1f2767854390923a8d25a2e4a191)](https://www.codacy.com/manual/wwkimball/yamlpath?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=wwkimball/yamlpath&amp;utm_campaign=Badge_Grade)

Along with providing a
[standard for defining YAML Paths](https://github.com/wwkimball/yamlpath/wiki/Segments-of-a-YAML-Path),
this project aims to provide
[generally-useful command-line tools](https://github.com/wwkimball/yamlpath/wiki/Command-Line-(CLI)-Tools)
which implement YAML Paths.  These bring intuitive YAML, EYAML, JSON, and
compatible data parsing and editing capabilties to the command-line.  It is
also a
[Python library](https://github.com/wwkimball/yamlpath/wiki/Python-Library)
for other projects to readily employ YAML Paths.

## Contents

1. [Introduction](#introduction)
2. [Illustration](#illustration)
3. [Installing](#installing)
4. [Supported YAML Path Segments](#supported-yaml-path-segments)
5. [Based on ruamel.yaml and Python 3](#based-on-ruamelyaml-and-python-3)
6. [The Files of This Project](#the-files-of-this-project)
   1. [Command-Line Tools](#command-line-tools)
   2. [Libraries](#libraries)
7. [Basic Usage](#basic-usage)
   1. [Basic Usage:  Command-Line Tools](#basic-usage--command-line-tools)
      1. [Rotate Your EYAML Keys](#rotate-your-eyaml-keys)
      2. [Get the Differences Between Two Documents](#get-the-differences-between-two-documents)
      3. [Get a YAML/JSON/Compatible Value](#get-a-yamljsoncompatible-value)
      4. [Search For YAML Paths](#search-for-yaml-paths)
      5. [Change a YAML/JSON/Compatible Value](#change-a-yamljsoncompatible-value)
      6. [Merge YAML/JSON/Compatible Files](#merge-yamljsoncompatible-files)
      7. [Validate YAML/JSON/Compatible Documents](#validate-yamljsoncompatible-documents)

   2. [Basic Usage:  Libraries](#basic-usage--libraries)
      1. [Initialize ruamel.yaml and These Helpers](#initialize-ruamelyaml-and-these-helpers)
      2. [Searching for YAML Nodes](#searching-for-yaml-nodes)
      3. [Changing Values](#changing-values)
      4. [Merging Documents](#merging-documents)

## Introduction

This project presents and utilizes YAML Paths, which are a powerful, intuitive
means of identifying one *or more* nodes within [YAML](https://yaml.org/),
[EYAML](https://github.com/voxpupuli/hiera-eyaml), or compatible data structures
like [JSON](https://www.json.org/).  Both dot-notation (inspired by
[Hiera](https://github.com/puppetlabs/hiera)) and forward-slash-notation
(influenced by [XPath](https://www.w3schools.com/xml/xml_xpath.asp)) are
supported.  The [libraries](#libraries) (modules) and several [command-line tool
implementations](#command-line-tools) are provided.  With these, you can build
YAML Path support right into your own application or easily use its capabilities
right away from the command-line to retrieve, update, merge, validate, and scan
YAML/JSON/Compatible data.

This implementation of YAML Path is a *query language* in addition to a *node
descriptor*.  With it, you can describe or select a single precise node or
search for any number of nodes that match some criteria.  Keys, values,
elements, anchors, and aliases can all be searched at any number of levels
within the data structure using the same query.  Collectors can also be used to
gather and further select from otherwise disparate parts of the source data.

The [project Wiki](https://github.com/wwkimball/yamlpath/wiki) provides a
deeper dive into these concepts.

## Illustration

To illustrate some of these concepts, consider these samples:

```yaml
---
hash:
  child_attr:
    key: 5280
```

This value, `5280`, can be identified via YAML Path as any of:

1. `hash.child_attr.key` (dot-notation)
2. `hash.child_attr[.=key]` (search all child keys for one named, `key`, and
   yield its value)
3. `/hash/child_attr/key` (same as 1 but in forward-slash notation)
4. `/hash/child_attr[.=key]` (same as 2 but in forward-slash notation)

```yaml
---
aliases:
  - &first_anchor Simple string value
```

With YAML Path, you can select this anchored value by any of these equivalent
expressions:

1. `aliases[0]` (explicit array element number)
2. `aliases.0` (implicit array element number in dot-notation)
3. `aliases[&first_anchor]` (search by Anchor name)
4. `aliases[.^Simple]` (search for any elements starting with "Simple")
5. `aliases[.%string]` (search for any elements containing "string")
6. `aliases[.$value]` (search for any elements ending with "value")
7. `aliases[.=~/^(\b[Ss][a-z]+\s){2}[a-z]+$/]` (search for any elements matching
   a complex Regular Expression, which happens to match the example)
8. `/aliases[0]` (same as 1 but in forward-slash notation)
9. `/aliases/0` (same as 2 but in forward-slash notation)
10. `/aliases[&first_anchor]` (same as 3 but in forward-slash notation)

```yaml
---
users:
  - name: User One
    password: ENC[PKCS7,MIIBiQY...Jk==]
    roles:
      - Writers
  - name: User Two
    password: ENC[PKCS7,MIIBiQY...vF==]
    roles:
      - Power Users
      - Editors
```

With an example like this, YAML Path enables:

* selection of single nodes: `/users/0/roles/0` = `Writers`
* all children nodes of any given parent: `/users/1/roles` =
  `["Power Users", "Editors"]`
* searching by a child attribute: `/users[name="User One"]/password` =
  `Some decrypted value, provided you have the appropriate EYAML keys`
* pass-through selections against arrays-of-hashes: `/users/roles` =
  `["Writers"]\n["Power Users", "Editors"]` (each user's list of roles are a
  seperate result)
* collection of disparate results: `(/users/name)` =
  `["User One", "User Two"]` (all names appear in a single result instead of
  one per line)

For a deeper exploration of YAML Path's capabilities, please visit the
[project Wiki](https://github.com/wwkimball/yamlpath/wiki).

## Supported YAML Path Segments

A YAML Path *segment* is the text between seperators which identifies zero or
more parent or leaf nodes within the data structure.  For dot-notation, a path
like `hash.key` identifies two segments:  `hash` (a parent node) and `key` (a
leaf node).  The same path in forward-slash notation would be:  `/hash/key`.

YAML Path understands these segment types:

* Top-level Hash key selection: `key`
* Explicit top-level array element selection: `[#]` where `#` is the zero-based
  element number; `#` can also be negative, causing the element to be selected
  from the end of the Array
* Implicit array element selection **or** numbered hash key selection: `#`
  where `#` is the 0-based element number **or** exact name of a hash key which
  is itself a number
* Top-level (Hash) Anchor lookups: `&anchor_name` (the `&` is required to
  indicate you are seeking an Anchor by name)
* Hash sub-keys:  `hash.child.key` or `/hash/child/key`
* Demarcation for dotted Hash keys:  `hash.'dotted.child.key'` or
  `hash."dotted.child.key"` (not necessary when using forward-slash notation,
  `/hash/dotted.child.key`)
* Named Array element selection:  `array[#]`, `array.#`, `/array[#]`, or
  `/array/#` where `array` is the name of the Hash key containing Array data
  and `#` is the 0-based element number
* Anchor lookups in named Arrays:  `array[&anchor_name]`  where `array` is the
  name of the Hash key containing Array data and both of the `[]` pair and `&`
  are required to indicate you are seeking an Anchor by name within an Array
* Array slicing: `array[start#:stop#]` where `start#` is the first inclusive,
  zero-based element and `stop#` is the last exclusive element to select;
  either or both can be negative, causing the elements to be selected from the
  end of the Array; when `start#` and `stop#` are identical, it is the same as
  `array[start#]`
* Hash slicing: `hash[min:max]` where `min` and `max` are alphanumeric terms
  between which the Hash's keys are compared
* Escape symbol recognition:  `hash.dotted\.child\.key`,
  `/hash/whacked\/child\/key`, and `keys_with_\\slashes`
* Hash attribute searches (which can return zero or more matches):
  * Exact match:  `hash[name=admin]`
  * Starts With match:  `hash[name^adm]`
  * Ends With match:  `hash[name$min]`
  * Contains match:  `hash[name%dmi]`
  * Less Than match: `hash[access_level<500]`
  * Greater Than match: `hash[access_level>0]`
  * Less Than or Equal match: `hash[access_level<=100]`
  * Greater Than or Equal match: `hash[access_level>=0]`
  * Regular Expression matches: `hash[access_level=~/^\D+$/]` (the `/` Regular
    Expression delimiter can be substituted for any character you need, except
    white-space; note that `/` does not interfere with forward-slash notation
    *and it does not need to be escaped* because the entire search expression is
    contained within a `[]` pair)
  * Invert any match with `!`, like: `hash[name!=admin]` or even
    `hash[!name=admin]` (the former syntax is used when YAML Paths are
    stringified but both forms are equivalent)
  * Demarcate and/or escape expression operands, like:
    `hash[full\ name="Some User\'s Name"]` (note that embedded, single `'` and
    `"` must be escaped lest they be deemed unmatched demarcation pairings)
  * Multi-level matching: `hash[name%admin].pass[encrypted!^ENC\[]` or
    `/hash[name%admin]/pass[encrypted!^ENC\[]`
  * Descendent node searches:
    `structure[has.descendant.with=something].has.another.field` or
    `/structure[/has/descendant/with=something]/has/another/field`
* Array element searches with all of the search methods above via `.` (yields
  any matching elements): `array[.>9000]`
* Hash key-name searches with all of the search methods above via `.` (yields
  their values, not the keys themselves): `hash[.^app_]`
* Array-of-Hashes Pass-Through Selection:  Omit a selector for the elements of
  an Array-of-Hashes and all matching Hash attributes at that level will be
  yielded (or searched when there is more to the path).  For example,
  `warriors[1].power_level` or `/warriors[1]/power_level` will return the
  power_level attribute of only the second Hash in an Array-of-Hashes while
  `warriors.power_level` or `/warriors/power_level` will return the power_level
  attribute of every Hash in the same Array-of-Hashes.  Of course these results
  can be filtered in multiple ways, like `warriors[power_level>9000]`,
  `/warriors[power_level>9000]`, `warriors.power_level[.>9000]`, and
  `/warriors/power_level[.>9000]` all yield only the power_level from *all*
  warriors with power_levels over 9,000 within the same array of warrior hashes.
* Wildcard Searches: The `*` symbol can be used as shorthand for the `[]`
  search operator against text keys and values: `/warriors/name/Go*`; it also
  returns every immediate child, regardless its key or value.
* Deep Traversals:  The `**` symbol pair deeply traverses the document:
  * When it is the last or only segment of a YAML Path, it selects every leaf
    node from the remainder of the document's tree: `/shows/**`
  * When another segment follows, it matches every node within the remainder
    of the document's tree for which the following (and subsequent) segments
    match: `/shows/**/name/Star*`
* Collectors:  Placing any portion of the YAML Path within parenthesis defines a
  virtual list collector, like `(YAML Path)`; concatenation and exclusion
  operators are supported -- `+` and `-`, respectively -- along with nesting,
  like `(...)-((...)+(...))`
* Complex combinations:
  `some::deep.hierarchy[with!=""].'any.valid'[.=~/(yaml|json)/][data%structure].or.complexity[4].2`
  or `/some::deep/hierarchy[with!=""]/any*.*valid[.=~/(yaml|json)/][data%structure]/or/compl*xity[4]/2/**`

This implementation of YAML Path encourages creativity.  Use whichever notation
and segment types that make the most sense to you in each application.

The [project Wiki provides more illustrative details of YAML Path Segments](https://github.com/wwkimball/yamlpath/wiki/Segments-of-a-YAML-Path).

## Installing

This project requires [Python](https://www.python.org/) 3.  It is tested
against Pythons 3.6 through 3.8.  Most operating systems and distributions
have access to Python 3 even if only Python 2 -- or no Python, at all -- came
pre-installed.  It is generally safe to have more than one version of Python
on your system at the same time, especially when using
[virtual Python environments](https://docs.python.org/3/library/venv.html).

Each published version of this project can be installed from
[PyPI](https://pypi.org/) using `pip`.  Note that on systems with more than one
version of Python, you will probably need to use `pip3`, or equivalent (e.g.:
Cygwin users may need to use `pip3.6`, `pip3.7`, `pip3.8`, or such).

```shell
pip3 install yamlpath
```

Note that very old versions of Python 3 ship with seriously outdated versions
of pip and setuptools.  You *must* update to at least **pip** version **18.1**
and **setuptools** version **46.4.0** to install yamlpath without
pre-installing its dependencies.  If you cannot update pip or setuptools, you
can still install yamlpath except you'll first need to install **ruamel.yaml**
like so:

```shell
# These commands CANNOT be joined, like: pip3.6 install ruamel.yaml yamlpath
pip3.6 install ruamel.yaml
pip3.6 install yamlpath
```

EYAML support is entirely optional.  You do not need EYAML to use YAML Path.
That YAML Path supports EYAML is a service to a substantial audience:  Puppet
users.  At the time of this writing, EYAML (classified as a Hiera
back-end/plug-in) is available only as a Ruby Gem.  That said, it provides a
command-line tool, `eyaml`, which can be employed by this otherwise Python
project.  To enjoy EYAML support, install compatible versions of ruby and
rubygems, then execute:

```shell
gem install hiera-eyaml
```

If this puts the `eyaml` command on your system `PATH`, nothing more need be
done apart from generating or obtaining your encryption keys.  Otherwise, you
can tell YAML Path library and tools where to find the `eyaml` command.

## Based on ruamel.yaml and Python 3

In order to support the best available YAML editing capability (so called,
round-trip editing with support for comment preservation), this project is based
on [ruamel.yaml](https://bitbucket.org/ruamel/yaml/overview) for
Python 3.  While ruamel.yaml is based on PyYAML --
Python's "standard" YAML library -- ruamel.yaml is [objectively better than
PyYAML](https://yaml.readthedocs.io/en/latest/pyyaml.html), which lacks critical
round-trip editing capabilities as well as up-to-date YAML/Compatible data
parsing capabilities (at the time of this writing).

Should PyYAML ever merge with -- or at least, catch up with -- ruamel.yaml, this
project can be (lightly) adapted to depend on it, instead.  These conversations
may offer some insight into when or whether this might happen:

* [Is this time to pass the baton?](https://github.com/yaml/pyyaml/issues/31)
* [Rebase off ruamel? - many new valuable features](https://github.com/yaml/pyyaml/issues/46)

## The Files of This Project

This repository contains:

1. Generally-useful Python library files.  These contain the reusable core of
   this project's YAML Path capabilities.
2. Some implementations of those libraries, exhibiting their capabilities and
   simple-to-use APIs as command-line tools.
3. Various support, documentation, and build files.

### Command-Line Tools

This project provides some command-line tool implementations which utilize YAML
Path.  For some use-case examples of these tools,
[see below](#basic-usage--command-line-tools).

The supplied command-line tools include:

* [eyaml-rotate-keys](yamlpath/commands/eyaml_rotate_keys.py)

```text
usage: eyaml-rotate-keys [-h] [-V] [-d | -v | -q] [-b] [-x EYAML]
                         -i OLDPRIVATEKEY -c OLDPUBLICKEY
                         -r NEWPRIVATEKEY -u NEWPUBLICKEY
                         YAML_FILE [YAML_FILE ...]

Rotates the encryption keys used for all EYAML values within a set of YAML
files, decrypting with old keys and re-encrypting using replacement keys.

positional arguments:
  YAML_FILE             one or more YAML files containing EYAML values

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -d, --debug           output debugging details
  -v, --verbose         increase output verbosity
  -q, --quiet           suppress all output except errors
  -b, --backup          save a backup of each modified YAML_FILE with an extra
                        .bak file-extension
  -x EYAML, --eyaml EYAML
                        the eyaml binary to use when it isn't on the PATH

EYAML_KEYS:
  All key arguments are required

  -r NEWPRIVATEKEY, --newprivatekey NEWPRIVATEKEY
                        the new EYAML private key
  -u NEWPUBLICKEY, --newpublickey NEWPUBLICKEY
                        the new EYAML public key
  -i OLDPRIVATEKEY, --oldprivatekey OLDPRIVATEKEY
                        the old EYAML private key
  -c OLDPUBLICKEY, --oldpublickey OLDPUBLICKEY
                        the old EYAML public key

Any YAML_FILEs lacking EYAML values will not be modified (or backed up, even
when -b/--backup is specified).
```

* [yaml-diff](yamlpath/commands/yaml_diff.py)

```text
usage: yaml-diff [-h] [-V] [-a] [-s | -o]
                 [-t ['.', '/', 'auto', 'dot', 'fslash']] [-x EYAML]
                 [-r PRIVATEKEY] [-u PUBLICKEY] [-E] [-d | -v | -q]
                 YAML_FILE YAML_FILE

Calculate the functional difference between two YAML/JSON/Compatible
documents. Immaterial differences (which YAML/JSON parsers discard) are
ignored. EYAML can be employed to compare encrypted values.

positional arguments:
  YAML_FILE             exactly two YAML/JSON/compatible files to compare; use
                        - to read one document from STDIN

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -a, --sync-arrays     Synchronize array elements before comparing them,
                        resulting only in ADD, DELETE, and SAME differences
                        (no CHANGEs because the positions of elements are
                        disregarded); Array-of-Hash elements must completely
                        and perfectly match or they will be deemed additions
                        or deletions
  -s, --same            Show all nodes which are the same in addition to
                        differences
  -o, --onlysame        Show only nodes which are the same, still reporting
                        that differences exist -- when they do -- with an
                        exit-state of 1
  -t ['.', '/', 'auto', 'dot', 'fslash'], --pathsep ['.', '/', 'auto', 'dot', 'fslash']
                        indicate which YAML Path seperator to use when
                        rendering results; default=dot
  -d, --debug           output debugging details
  -v, --verbose         increase output verbosity
  -q, --quiet           suppress all output except system errors

EYAML options:
  Left unset, the EYAML keys will default to your system or user defaults.
  Both keys must be set either here or in your system or user EYAML
  configuration file when using EYAML.

  -x EYAML, --eyaml EYAML
                        the eyaml binary to use when it isn't on the PATH
  -r PRIVATEKEY, --privatekey PRIVATEKEY
                        EYAML private key
  -u PUBLICKEY, --publickey PUBLICKEY
                        EYAML public key
  -E, --ignore-eyaml-values
                        Do not use EYAML to compare encrypted data; rather,
                        treat ENC[...] values as regular strings

Only one YAML_FILE may be the - pseudo-file for reading from STDIN. For more
information about YAML Paths, please visit
https://github.com/wwkimball/yamlpath.
```

* [yaml-get](yamlpath/commands/yaml_get.py)

```text
usage: yaml-get [-h] [-V] -p YAML_PATH
                [-t ['.', '/', 'auto', 'dot', 'fslash']] [-S] [-x EYAML]
                [-r PRIVATEKEY] [-u PUBLICKEY] [-d | -v | -q]
                [YAML_FILE]

Retrieves one or more values from a YAML/JSON/Compatible file at a specified
YAML Path. Output is printed to STDOUT, one line per result. When a result is
a complex data-type (Array or Hash), a JSON dump is produced to represent it.
EYAML can be employed to decrypt the values.

positional arguments:
  YAML_FILE             the YAML file to query; omit or use - to read from
                        STDIN

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -t ['.', '/', 'auto', 'dot', 'fslash'], --pathsep ['.', '/', 'auto', 'dot', 'fslash']
                        indicate which YAML Path seperator to use when
                        rendering results; default=dot
  -S, --nostdin         Do not implicitly read from STDIN, even when YAML_FILE
                        is not set and the session is non-TTY
  -d, --debug           output debugging details
  -v, --verbose         increase output verbosity
  -q, --quiet           suppress all output except errors

required settings:
  -p YAML_PATH, --query YAML_PATH
                        YAML Path to query

EYAML options:
  Left unset, the EYAML keys will default to your system or user defaults.
  Both keys must be set either here or in your system or user EYAML
  configuration file when using EYAML.

  -x EYAML, --eyaml EYAML
                        the eyaml binary to use when it isn't on the PATH
  -r PRIVATEKEY, --privatekey PRIVATEKEY
                        EYAML private key
  -u PUBLICKEY, --publickey PUBLICKEY
                        EYAML public key

For more information about YAML Paths, please visit
https://github.com/wwkimball/yamlpath.
```

* [yaml-merge](yamlpath/commands/yaml_merge.py)

```text
usage: yaml-merge [-h] [-V] [-c CONFIG] [-a {stop,left,right,rename}]
                  [-A {all,left,right,unique}] [-H {deep,left,right}]
                  [-O {all,deep,left,right,unique}] [-m YAML_PATH]
                  [-o OUTPUT | -w OVERWRITE] [-b] [-D {auto,json,yaml}] [-S]
                  [-d | -v | -q]
                  [YAML_FILE [YAML_FILE ...]]

Merges two or more YAML/JSON/Compatible files together.

positional arguments:
  YAML_FILE             one or more YAML files to merge, order-significant;
                        omit or use - to read from STDIN

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -c CONFIG, --config CONFIG
                        INI syle configuration file for YAML Path specified
                        merge control options
  -a {stop,left,right,rename}, --anchors {stop,left,right,rename}
                        means by which Anchor name conflicts are resolved
                        (overrides [defaults]anchors set via --config|-c and
                        cannot be overridden by [rules] because Anchors apply
                        to the whole file); default=stop
  -A {all,left,right,unique}, --arrays {all,left,right,unique}
                        default means by which Arrays are merged together
                        (overrides [defaults]arrays but is overridden on a
                        YAML Path basis via --config|-c); default=all
  -H {deep,left,right}, --hashes {deep,left,right}
                        default means by which Hashes are merged together
                        (overrides [defaults]hashes but is overridden on a
                        YAML Path basis in [rules] set via --config|-c);
                        default=deep
  -O {all,deep,left,right,unique}, --aoh {all,deep,left,right,unique}
                        default means by which Arrays-of-Hashes are merged
                        together (overrides [defaults]aoh but is overridden on
                        a YAML Path basis in [rules] set via --config|-c);
                        default=all
  -m YAML_PATH, --mergeat YAML_PATH
                        YAML Path indicating where in left YAML_FILE the right
                        YAML_FILE content is to be merged; default=/
  -o OUTPUT, --output OUTPUT
                        Write the merged result to the indicated nonexistent
                        file
  -w OVERWRITE, --overwrite OVERWRITE
                        Write the merged result to the indicated file; will
                        replace the file when it already exists
  -b, --backup          save a backup OVERWRITE file with an extra .bak
                        file-extension; applies only to OVERWRITE
  -D {auto,json,yaml}, --document-format {auto,json,yaml}
                        Force the merged result to be presented in one of the
                        supported formats or let it automatically match the
                        known file-name extension of OUTPUT|OVERWRITE (when
                        provided), or match the type of the first document;
                        default=auto
  -S, --nostdin         Do not implicitly read from STDIN, even when there are
                        no - pseudo-files in YAML_FILEs with a non-TTY session
  -d, --debug           output debugging details
  -v, --verbose         increase output verbosity
  -q, --quiet           suppress all output except errors (implied when
                        -o|--output is not set)

            The CONFIG file is an INI file with up to three sections:
            [defaults] Sets equivalents of -a|--anchors, -A|--arrays,
                       -H|--hashes, and -O|--aoh.
            [rules]    Each entry is a YAML Path assigning -A|--arrays,
                       -H|--hashes, or -O|--aoh for precise nodes.
            [keys]     Wherever -O|--aoh=DEEP, each entry is treated as a
                       record with an identity key.  In order to match RHS
                       records to LHS records, a key must be known and is
                       identified on a YAML Path basis via this section.
                       Where not specified, the first attribute of the first
                       record in the Array-of-Hashes is presumed the identity
                       key for all records in the set.

            The left-to-right order of YAML_FILEs is significant.  Except
            when this behavior is deliberately altered by your options, data
            from files on the right overrides data in files to their left.
            Only one input file may be the - pseudo-file (read from STDIN).
            When no YAML_FILEs are provided, - will be inferred as long as you
            are running this program without a TTY (unless you set
            --nostdin|-S).  Any file, including input from STDIN, may be a
            multi-document YAML or JSON file.

            For more information about YAML Paths, please visit
            https://github.com/wwkimball/yamlpath.
```

* [yaml-paths](yamlpath/commands/yaml_paths.py)

```text
usage: yaml-paths [-h] [-V] -s EXPRESSION [-c EXPRESSION] [-m] [-L] [-F] [-X]
                  [-P] [-t ['.', '/', 'auto', 'dot', 'fslash']] [-i | -k | -K]
                  [-a] [-A | -Y | -y | -l] [-e] [-x EYAML] [-r PRIVATEKEY]
                  [-u PUBLICKEY] [-S] [-d | -v | -q]
                  [YAML_FILE [YAML_FILE ...]]

Returns zero or more YAML Paths indicating where in given YAML/JSON/Compatible
data one or more search expressions match. Values, keys, and/or anchors can be
searched. EYAML can be employed to search encrypted values.

positional arguments:
  YAML_FILE             one or more YAML files to search; omit or use - to
                        read from STDIN

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -c EXPRESSION, --except EXPRESSION
                        except results matching this search expression; can be
                        set more than once
  -m, --expand          expand matching parent nodes to list all permissible
                        child leaf nodes (see "reference handling options" for
                        restrictions)
  -t ['.', '/', 'auto', 'dot', 'fslash'], --pathsep ['.', '/', 'auto', 'dot', 'fslash']
                        indicate which YAML Path seperator to use when
                        rendering results; default=dot
  -a, --refnames        also search the names of &anchor and *alias references
  -S, --nostdin         Do not implicitly read from STDIN, even when there are
                        no - pseudo-files in YAML_FILEs with a non-TTY session
  -d, --debug           output debugging details
  -v, --verbose         increase output verbosity
  -q, --quiet           suppress all non-result output except errors

required settings:
  -s EXPRESSION, --search EXPRESSION
                        the search expression; can be set more than once

result printing options:
  -L, --values          print the values or elements along with each YAML Path
                        (complex results are emitted as JSON; use --expand to
                        emit only simple values)
  -F, --nofile          omit source file path and name decorators from the
                        output (applies only when searching multiple files)
  -X, --noexpression    omit search expression decorators from the output
  -P, --noyamlpath      omit YAML Paths from the output (useful with --values
                        or to indicate whether a file has any matches without
                        printing them all, perhaps especially with
                        --noexpression)

key name searching options:
  -i, --ignorekeynames  (default) do not search key names
  -k, --keynames        search key names in addition to values and array
                        elements
  -K, --onlykeynames    only search key names (ignore all values and array
                        elements)

reference handling options:
  Indicate how to treat anchor and alias references. An anchor is an
  original, reusable key or value. All aliases become replaced by the
  anchors they reference when YAML data is read. These options specify how
  to handle this duplication of keys and values. Note that the default
  behavior includes all aliased keys but not aliased values.

  -A, --anchorsonly     include only original matching key and value anchors
                        in results, discarding all aliased keys and values
                        (including child nodes)
  -Y, --allowkeyaliases
                        (default) include matching key aliases, permitting
                        search traversal into their child nodes
  -y, --allowvaluealiases
                        include matching value aliases (does not permit search
                        traversal into aliased keys)
  -l, --allowaliases    include all matching key and value aliases

EYAML options:
  Left unset, the EYAML keys will default to your system or user defaults.
  Both keys must be set either here or in your system or user EYAML
  configuration file when using EYAML.

  -e, --decrypt         decrypt EYAML values in order to search them
                        (otherwise, search the encrypted blob)
  -x EYAML, --eyaml EYAML
                        the eyaml binary to use when it isn't on the PATH
  -r PRIVATEKEY, --privatekey PRIVATEKEY
                        EYAML private key
  -u PUBLICKEY, --publickey PUBLICKEY
                        EYAML public key

A search or exception EXPRESSION takes the form of a YAML Path search operator
-- %, $, =, ^, >, <, >=, <=, =~, or ! -- followed by the search term, omitting
the left-hand operand. For more information about YAML Paths, please visit
https://github.com/wwkimball/yamlpath.
```

* [yaml-set](yamlpath/commands/yaml_set.py)

```text
usage: yaml-set [-h] [-V] -g YAML_PATH
                [-a VALUE | -f FILE | -i | -R LENGTH | -D]
                [-F {bare,boolean,default,dquote,float,folded,int,literal,squote}]
                [-c CHECK] [-s YAML_PATH] [-m] [-b]
                [-t ['.', '/', 'auto', 'dot', 'fslash']] [-M CHARS] [-e]
                [-x EYAML] [-r PRIVATEKEY] [-u PUBLICKEY] [-S] [-d | -v | -q]
                [YAML_FILE]

Changes one or more Scalar values in a YAML/JSON/Compatible document at a
specified YAML Path. Matched values can be checked before they are replaced to
mitigate accidental change. When matching singular results, the value can be
archived to another key before it is replaced. Further, EYAML can be employed
to encrypt the new values and/or decrypt an old value before checking it.

positional arguments:
  YAML_FILE             the YAML file to update; omit or use - to read from
                        STDIN

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -F {bare,boolean,default,dquote,float,folded,int,literal,squote}, --format {bare,boolean,default,dquote,float,folded,int,literal,squote}
                        override automatic formatting of the new value
  -c CHECK, --check CHECK
                        check the value before replacing it
  -s YAML_PATH, --saveto YAML_PATH
                        save the old value to YAML_PATH before replacing it;
                        implies --mustexist
  -m, --mustexist       require that the --change YAML_PATH already exist in
                        YAML_FILE
  -b, --backup          save a backup YAML_FILE with an extra .bak file-
                        extension
  -t ['.', '/', 'auto', 'dot', 'fslash'], --pathsep ['.', '/', 'auto', 'dot', 'fslash']
                        indicate which YAML Path seperator to use when
                        rendering results; default=dot
  -M CHARS, --random-from CHARS
                        characters from which to build a value for --random;
                        default=all upper- and lower-case letters and all
                        digits
  -S, --nostdin         Do not implicitly read from STDIN, even when there is
                        no YAML_FILE with a non-TTY session
  -d, --debug           output debugging details
  -v, --verbose         increase output verbosity
  -q, --quiet           suppress all output except errors

required settings:
  -g YAML_PATH, --change YAML_PATH
                        YAML Path where the target value is found

input options:
  -a VALUE, --value VALUE
                        set the new value from the command-line instead of
                        STDIN
  -f FILE, --file FILE  read the new value from file (discarding any trailing
                        new-lines)
  -i, --stdin           accept the new value from STDIN (best for sensitive
                        data)
  -R LENGTH, --random LENGTH
                        randomly generate a replacement value of a set length
  -D, --delete          delete rather than change target node(s)

EYAML options:
  Left unset, the EYAML keys will default to your system or user defaults.
  You do not need to supply a private key unless you enable --check and the
  old value is encrypted.

  -e, --eyamlcrypt      encrypt the new value using EYAML
  -x EYAML, --eyaml EYAML
                        the eyaml binary to use when it isn't on the PATH
  -r PRIVATEKEY, --privatekey PRIVATEKEY
                        EYAML private key
  -u PUBLICKEY, --publickey PUBLICKEY
                        EYAML public key

When no changes are made, no backup is created, even when -b/--backup is
specified. For more information about YAML Paths, please visit
https://github.com/wwkimball/yamlpath.
```

* [yaml-validate](yamlpath/commands/yaml_validate.py)

```text
usage: yaml-validate [-h] [-V] [-S] [-d | -v | -q] [YAML_FILE [YAML_FILE ...]]

Validate YAML, JSON, and compatible files.

positional arguments:
  YAML_FILE      one or more single- or multi-document YAML/JSON/compatible
                 files to validate; omit or use - to read from STDIN

optional arguments:
  -h, --help     show this help message and exit
  -V, --version  show program's version number and exit
  -S, --nostdin  Do not implicitly read from STDIN, even when there are no -
                 pseudo-files in YAML_FILEs with a non-TTY session
  -d, --debug    output debugging details
  -v, --verbose  increase output verbosity (show valid documents)
  -q, --quiet    suppress all output except system errors

Except when suppressing all report output with --quiet|-q, validation issues
are printed to STDOUT (not STDERR). Further, the exit-state will report 0 when
there are no issues, 1 when there is an issue with the supplied command-line
arguments, or 2 when validation has failed for any document.
```

### Libraries

While there are several supporting library files like enumerations, types, and
exceptions, the most interesting library files include:

* [yamlpath.py](yamlpath/yamlpath.py) -- The core YAML Path parser logic.
* [processor.py](yamlpath/processor.py) -- Processes YAMLPath instances to read
  or write data to YAML/Compatible sources.
* [eyamlprocessor.py](yamlpath/eyaml/eyamlprocessor.py) -- Extends the
  Processor class to support EYAML data encryption and decryption.
* [merger.py](merger/merger.py) -- The core document merging logic.

## Basic Usage

The files of this project can be used either as command-line tools or as
libraries to supplement your own work.

### Basic Usage:  Command-Line Tools

The command-line tools are self-documented and [their documentation is captured
above](#command-line-tools) for easy reference.  Simply pass `--help` to them in
order to obtain the same detailed documentation.

Please review [the comprehensive test_commands_*.py unit tests](/tests/) to
explore samples of YAML files and the many ways these tools help get and set
their data.

The following are some simple examples of their typical use-cases.

#### Rotate Your EYAML Keys

If the eyaml command is already on your PATH (if not, be sure to also supply
the optional `--eyaml` or `-x` argument):

```shell
eyaml-rotate-keys \
  --oldprivatekey=~/old-keys/private_key.pkcs7.pem \
  --oldpublickey=~/old-keys/public_key.pkcs7.pem \
  --newprivatekey=~/new-keys/private_key.pkcs7.pem \
  --newpublickey=~/new-keys/public_key.pkcs7.pem \
  my_1st_yaml_file.yaml my_2nd_yaml_file.eyaml ... my_Nth_yaml_file.yaml
```

You could combine this with `find` and `xargs` if your E/YAML file are
dispersed through a directory hierarchy, as with Hiera data.

##### EYAML Compatibility Alert

The maintainers of the hiera-eyaml project have released version 3.x and it is
*not backward compatible* with encryption certificates generated for
hiera-eyaml version 2.x.  This has nothing to do with YAML Path and is alerted
here only as a courtesy to YAML Path users.  **If you upgrade your
installation of hiera-eyaml without first updating your encryption
certificates and using a tool like eyaml-rotate-keys (provided here) to
re-encrypt your data with the replacement certificates, hiera-eyaml 3.x will
fail to decrypt your data!**  This is *not* a problem with YAML Path.
hiera-eyaml certificate compatibility is well outside the purview of YAML Path
and its tools.

#### Get the Differences Between Two Documents

For routine use:

```shell
yaml-diff yaml_file1.yaml yaml_file2.yaml
```

Output is very similar to that of standard GNU diff against text files, except
it is generated against the *data* within the input files.  This excludes
evaluating purely structural and immaterial differences between them like value
demarcation, white-space, and comments.  When you need to evaluate the two
files as if they were just text files, use GNU diff or any of its clones.

To see all identical entries along with differences:

```shell
yaml-diff --same yaml_file1.yaml yaml_file2.yaml
```

To see *only* entries which are identical between the documents:

```shell
yaml-diff --onlysame yaml_file1.yaml yaml_file2.yaml
```

Advanced:  Arrays can be evaluated such that they are synchronized before
evaluation.  Rather than compare elements by identical index in both
documents -- reporting differences between them as changes and any additional
elements as additions or deletions -- they can instead be compared by matching
up all identical elements and then reporting only those values which are unique
to either document (and optionally identical matches).

```shell
yaml-diff --sync-arrays yaml_file1.yaml yaml_file2.yaml
```

#### Get a YAML/JSON/Compatible Value

At its simplest:

```shell
yaml-get \
  --query=see.documentation.above.for.many.samples \
  my_yaml_file.yaml
```

#### Search For YAML Paths

Simplest use:

```shell
yaml-paths \
  --search=%word \
  /some/directory/*.yaml
```

Search for multiple expressions and exclude unwanted results:

```shell
yaml-paths \
  --search=^another \
  --search=$word \
  --except=%bad \
  /some/directory/*.yaml
```

Return all leaf nodes under matching parents (most useful when matching against Hash keys and you only want the original leaf nodes beneath them):

```shell
yaml-paths \
  --expand \
  --keynames \
  --search==parent_node \
  /some/directory/*.yaml
```

#### Change a YAML/JSON/Compatible Value

For a no-frills change to a YAML file with deeply nested Hash structures:

```shell
yaml-set \
  --change=see.documentation.above.for.many.samples \
  --value="New Value" \
  my_yaml_file.yaml
```

To rotate a password, preserving the old password perhaps so your automation can
apply the new password to your application(s):

```shell
yaml-set \
  --mustexist \
  --change=the.new.password \
  --saveto=the.old.password \
  --value="New Password" \
  my_yaml_file.yaml
```

For the extremely cautious, you could check the old password before rotating
it and save a backup of the original file:

```shell
yaml-set \
  --mustexist \
  --change=the.new.password \
  --saveto=the.old.password \
  --check="Old Password" \
  --value="New Password" \
  --backup \
  my_yaml_file.yaml
```

You can also add EYAML encryption (assuming the `eyaml` command is on your
PATH; if not, you can pass `--eyaml` to specify its location).  In this example,
I add the optional `--format=folded` so that the long EYAML value is broken up
into a multi-line value rather than one very long string.  This is the preferred
format for human legibility as well as EYAML consumers like
[Puppet](http://puppet.com).  Note that `--format` has several other settings
and applies only to new values.

```shell
yaml-set \
  --change=the.new.password \
  --mustexist \
  --saveto=the.old.password \
  --check="Old Password" \
  --value="New Password" \
  --eyamlcrypt \
  --format=folded \
  --backup \
  my_yaml_file.yaml
```

You can even tell EYAML which keys to use, if not your default system or user
keys:

```shell
yaml-set \
  --change=the.new.password \
  --mustexist \
  --saveto=the.old.password \
  --check="Old Password" \
  --value="New Password" \
  --eyamlcrypt \
  --format=folded \
  --privatekey=/secret/keys/private_key.pkcs7.pem \
  --publickey=/secret/keys/public_key.pkcs7.pem \
  --backup \
  my_yaml_file.yaml
```

Note that for even greater security scenarios, you can keep the new value off of
your command-line, process list, and command history by swapping out `--value`
for one of `--stdin`, `--file`, or even `--random LENGTH` (use Python's
strongest random value generator if you don't need to specify the replacement
value in advance).

#### Merge YAML/JSON/Compatible Files

At its simplest, the `yaml-merge` command accepts two or more input files and
merges them together from left-to-right, writing the result to STDOUT:

```shell
yaml-merge leftmost.yaml middle.yaml right.json
```

If you'd rather write the results to a new output file (which must not already
exist):

```shell
yaml-merge \
  --output=newfile.yaml \
  leftmost.yaml \
  middle.yaml \
  right.json
```

Should you wish to merge the content of the files into a specific location (or
even multiple locations) within the leftmost document, specify a YAML Path via
the `--mergeat` or `-m` argument:

```shell
yaml-merge \
  --mergeat=/anywhere/within/the/document \
  leftmost.yaml \
  middle.yaml \
  right.json
```

To write arbitrary data from STDIN into a document, use the `-` pseudo-file:

```shell
echo "{arbitrary: [document, structure]}" | yaml-merge target.yaml -
```

Combine `--mergeat` or `-m` with the STDIN pseudo-file to control where the
data is to be written:

```shell
echo "{arbitrary: [document, structure]}" | \
  yaml-merge \
    --mergeat=/anywhere/within/the/document \
    target.yaml -
```

There are many options for precisely controlling how the merge is performed,
including the ability to specify complex rules on a YAML Path basis via a
configuration file.  Review the command's `--help` or the
[related Wiki](https://github.com/wwkimball/yamlpath/wiki/yaml-merge) for
more detail.

#### Validate YAML/JSON/Compatible Documents

Validating the structure of YAML, JSON, and compatible files is as simple as
running:

```shell
yaml-validate /path/to/any/files.yaml /path/to/more/files.json
```

In this default configuration, the command will output no report when all input
documents are valid.  It will also report an exit-state of zero (0).  Should
there be any validation errors, each will be printed to the screen and the
exit-state will be 2.  An exit-state of 1 means your command-line arguments
were incorrect and an appropritae user error message will be displayed.

When there are validation issues, the offending file-name(s) and sub-document
index(es) (zero-based) will be displayed along with a detailed validation error
message.

### Basic Usage:  Libraries

As for the libraries, they are also heavily documented and the example
implementations may perhaps serve as good copy-paste fodder (provided you give
credit to the source).  That said, here's a general flow/synopsis.

#### Initialize ruamel.yaml and These Helpers

Your preferences may differ, but I use this setup for round-trip YAML parsing
and editing with ruamel.yaml.  When you need to process EYAML encrypted data,
replace `yamlpath.Processor` with `yamlpath.eyaml.EYAMLProcessor` and add error
handling for `yamlpath.eyaml.EYAMLCommandException`.

Note that `import yamlpath.patches` is entirely optional.  I wrote and use it to
block ruamel.yaml's Emitter from injecting unnecessary newlines into folded
values (it improperly converts every single new-line into two for left-flushed
multi-line values, at the time of this writing).  Since "block" output EYAML
values are left-flushed multi-line folded strings, this fix is necessary when
using EYAML features.  At least, until ruamel.yaml has its own fix for this
issue.

Note also that these examples use `ConsolePrinter` to handle STDOUT and STDERR
messaging.  You don't have to.  However, some kind of logger must be passed to
these libraries so they can write messages _somewhere_.  Your custom message
handler or logger must provide the same API as `ConsolePrinter`; review the
header documentation in [consoleprinter.py](yamlpath/wrappers/consoleprinter.py)
for details.  Generally speaking, it would be trivial to write your own custom
wrapper for Python's standard logging facilities if you require targets other
than STDOUT and STDERR.

```python
import sys

from ruamel.yaml import YAML
from ruamel.yaml.parser import ParserError

import yamlpath.patches
from yamlpath.func import get_yaml_data, get_yaml_editor
from yamlpath.wrappers import ConsolePrinter
from yamlpath import Processor

# Process command-line arguments and initialize the output writer
args = processcli()
log = ConsolePrinter(args)

# Prep the YAML parser and round-trip editor (tweak to your needs)
yaml = get_yaml_editor()

# At this point, you'd load or parse your YAML file, stream, or string.  When
# loading from file, I typically follow this pattern:
(yaml_data, doc_loaded) = get_yaml_data(yaml, log, yaml_file)
if not doc_loaded:
    # There was an issue loading the file; an error message has already been
    # printed.
    exit(1)

# Pass the log writer and parsed YAML data to the YAMLPath processor
processor = Processor(log, yaml_data)

# At this point, the processor is ready to handle YAMLPaths
```

#### Searching for YAML Nodes

These libraries use [Generators](https://wiki.python.org/moin/Generators) to get
nodes from parsed YAML data.  Identify which node(s) to get via YAML Path
strings.  You should also catch `yamlpath.exceptions.YAMLPathException`s
unless you prefer Python's native stack traces.  When using EYAML, you should
also catch `yamlpath.eyaml.exceptions.EYAMLCommandException`s for the same
reason.  Whether you are working with a single result or many, you should
consume the Generator output with a pattern similar to:

```python
from yamlpath import YAMLPath
from yamlpath.exceptions import YAMLPathException

yaml_path = YAMLPath("see.documentation.above.for.many.samples")
try:
    for node_coordinate in processor.get_nodes(yaml_path):
        log.debug("Got {} from '{}'.".format(node_coordinate, yaml_path))
        # Do something with each node_coordinate.node (the actual data)
except YAMLPathException as ex:
    # If merely retrieving data, this exception may be deemed non-critical
    # unless your later code absolutely depends upon a result.
    log.error(ex)
```

#### Changing Values

At its simplest, you only need to supply the the YAML Path to one or more nodes
to update, and the value to apply to them.  Catching
`yamlpath.exceptions.YAMLPathException` is optional but usually preferred over
allowing Python to dump the call stack in front of your users.  When using
EYAML, the same applies to `yamlpath.eyaml.exceptions.EYAMLCommandException`.

```python
from yamlpath.exceptions import YAMLPathException

try:
    processor.set_value(yaml_path, new_value)
except YAMLPathException as ex:
    log.critical(ex, 119)
except EYAMLCommandException as ex:
    log.critical(ex, 120)
```

#### Merging Documents

A document merge naturally requires at least two documents.  At the code-level,
this means two populated DOM objects (populated instances of `yaml_data` from
above).  You do not need to use a `Processor` for merging.  In the least amount
of code, a merge looks like:

```python
from yamlpath.exceptions import YAMLPathException
from yamlpath.merger.exceptions import MergeException
from yamlpath.merger import Merger, MergerConfig

# Obtain or build the lhs_data and rhs_data objects using get_yaml_data or
# equivalent.

# You'll still need to supply a logger and some arguments used by the merge
# engine.  For purely default behavior, you could create args as a bare
# SimpleNamespace.  Initialize the new Merger instance with the LHS document.
merger = Merger(log, lhs_data, MergerConfig(log, args))

# Merge RHS into LHS
try:
    merger.merge_with(rhs_data)
except MergeException as mex:
    log.critical(mex, 129)
except YAMLPathException as yex:
    log.critical(yex, 130)

# At this point, merger.data is the merged result; do what you will with it,
# including merging more data into it.  When you are ready to dump (write)
# out the merged data, you must prepare the document and your
# ruamel.yaml.YAML instance -- usually obtained from func.get_yaml_editor()
# -- like this:
merger.prepare_for_dump(my_yaml_editor)
```
