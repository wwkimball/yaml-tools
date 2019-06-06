# YAML Path and Command-Line Tools

[![Build Status](https://travis-ci.org/wwkimball/yamlpath.svg?branch=master)](https://travis-ci.org/wwkimball/yamlpath)
[![Python versions](https://img.shields.io/pypi/pyversions/yamlpath.svg)](https://pypi.org/project/yamlpath/)
[![PyPI version](https://badge.fury.io/py/yamlpath.svg)](https://pypi.org/project/yamlpath/)
[![Coverage Status](https://coveralls.io/repos/github/wwkimball/yamlpath/badge.svg?branch=master)](https://coveralls.io/github/wwkimball/yamlpath?branch=master)

Contents:

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
      2. [Get a YAML Value](#get-a-yaml-value)
      3. [Change a YAML Value](#change-a-yaml-value)
   2. [Basic Usage:  Libraries](#basic-usage--libraries)
      1. [Initialize ruamel.yaml and These Helpers](#initialize-ruamelyaml-and-these-helpers)
      2. [Searching for YAML Nodes](#searching-for-yaml-nodes)
      3. [Changing Values](#changing-values)

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
right away from the command-line to retrieve or update YAML/Compatible data.

This implementation of YAML Path is a *query language* in addition to a *node
descriptor*.  With it, you can describe or select a single precise node or
search for any number of nodes that match some criteria.  Keys, values, and
elements can all be searched at any number of levels within the data structure
using the same query.  Collectors can also be used to gather and further select
from otherwise disparate parts of the source data.

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

A YAML Path *segment* is the text between seperators which identifies a parent
or leaf node within the data structure.  For dot-notation, a path like
`hash.key` identifies two segments:  `hash` (a parent node) and `key` (a leaf
node).  The same path in forward-slash notation would be:  `/hash/key`.

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
* Collectors:  Placing any portion of the YAML Path within parenthesis defines a
  virtual list collector, like `(YAML Path)`; concatenation and exclusion
  operators are supported -- `+` and `-`, respectively -- along with nesting,
  like `(...)-((...)+(...))`
* Complex combinations:
  `some::deep.hierarchy[with!=""].'any.valid'[.=~/(yaml|json)/][data%structure].or.complexity[4].2`
  or `/some::deep/hierarchy[with!=""]/any.valid[.=~/(yaml|json)/][data%structure]/or/complexity[4]/2`

This implementation of YAML Path encourages creativity.  Use whichever notation
and segment types that make the most sense to you in each application.

## Installing

This project requires [Python](https://www.python.org/) 3.6.  Most operating
systems and distributions have access to Python 3 even if only Python 2 -- or
no Python, at all -- came pre-installed.  It is generally safe to have more
than one version of Python on your system at the same time, especially when
using
[virtual Python environments](https://docs.python.org/3/library/venv.html).

Each published version of this project can be installed from
[PyPI](https://pypi.org/) using `pip`.  Note that on systems with more than one
version of Python, you will probably need to use `pip3`, or equivalent (e.g.:
Cygwin users may need to use `pip3.6`).

```shell
pip3 install yamlpath
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
Python 3.6.  While ruamel.yaml is based on PyYAML --
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

* [yaml-get](yamlpath/commands/yaml_get.py)

```text
usage: yaml-get [-h] [-V] -p YAML_PATH
                [-t ['.', '/', 'auto', 'dot', 'fslash']] [-x EYAML]
                [-r PRIVATEKEY] [-u PUBLICKEY] [-d | -v | -q]
                YAML_FILE

Retrieves one or more values from a YAML file at a specified YAML Path. Output
is printed to STDOUT, one line per result. When a result is a complex data-
type (Array or Hash), a JSON dump is produced to represent it. EYAML can be
employed to decrypt the values.

positional arguments:
  YAML_FILE             the YAML file to query

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -t ['.', '/', 'auto', 'dot', 'fslash'], --pathsep ['.', '/', 'auto', 'dot', 'fslash']
                        indicate which YAML Path seperator to use when
                        rendering results; default=dot
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

* [yaml-paths](yamlpath/commands/yaml_paths.py)

```text
usage: yaml-paths [-h] [-V] -s EXPRESSION [-c EXPRESSION] [-d | -v | -q] [-p]
                  [-t ['.', '/', 'auto', 'dot', 'fslash']] [-a] [-i | -k | -n]
                  [-o | -l] [-e] [-x EYAML] [-r PRIVATEKEY] [-u PUBLICKEY]
                  YAML_FILE [YAML_FILE ...]

Returns zero or more YAML Paths indicating where in given YAML/Compatible data
one or more search expressions match. Values, keys, and/or anchors can be
searched. EYAML can be employed to search encrypted values.

positional arguments:
  YAML_FILE             one or more YAML files to search

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -c EXPRESSION, --except EXPRESSION
                        except results matching this search expression; can be
                        set more than once
  -d, --debug           output debugging details
  -v, --verbose         increase output verbosity
  -q, --quiet           suppress all non-result output except errors
  -p, --pathonly        print results without any search expression decorators
  -t ['.', '/', 'auto', 'dot', 'fslash'], --pathsep ['.', '/', 'auto', 'dot', 'fslash']
                        indicate which YAML Path seperator to use when
                        rendering results; default=dot
  -a, --anchors         search anchor names

required settings:
  -s EXPRESSION, --search EXPRESSION
                        the search expression; can be set more than once

Key name searching options:
  -i, --ignorekeynames  (default) do not search key names
  -k, --keynames        search key names in addition to values and array
                        elements
  -n, --onlykeynames    only search key names (ignore all values and array
                        elements)

Duplicate alias options:
  An 'anchor' is an original, reusable key or value. An 'alias' is a copy of
  an 'anchor'. These options specify how to handle this duplication.

  -o, --originals       (default) include only the original anchor in matching
                        results
  -l, --duplicates      include anchor and duplicate aliases in results

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
usage: yaml-set [-h] [-V] -g YAML_PATH [-a VALUE | -f FILE | -i | -R LENGTH]
                [-F {bare,boolean,default,dquote,float,folded,int,literal,squote}]
                [-c CHECK] [-s YAML_PATH] [-m] [-b]
                [-t ['.', '/', 'auto', 'dot', 'fslash']] [-e] [-x EYAML]
                [-r PRIVATEKEY] [-u PUBLICKEY] [-d | -v | -q]
                YAML_FILE

Changes one or more values in a YAML file at a specified YAML Path. Matched
values can be checked before they are replaced to mitigate accidental change.
When matching singular results, the value can be archived to another key
before it is replaced. Further, EYAML can be employed to encrypt the new
values and/or decrypt an old value before checking them.

positional arguments:
  YAML_FILE             the YAML file to update

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

### Libraries

While there are several supporting library files like enumerations, types, and
exceptions, the most interesting library files include:

* [yamlpath.py](yamlpath/yamlpath.py) -- The core YAML Path parser logic.
* [processor.py](yamlpath/processor.py) -- Processes YAMLPath instances to read
  or write data to YAML/Compatible sources.
* [eyamlprocessor.py](yamlpath/eyaml/eyamlprocessor.py) -- Extends the
  Processor class to support EYAML data encryption and decryption.

## Basic Usage

The files of this project can be used either as command-line tools or as
libraries to supplement your own work.

### Basic Usage:  Command-Line Tools

The command-line tools are self-documented and [their documentation is captured
above](#command-line-tools) for easy reference.  Simply pass `--help` to them in
order to obtain the same detailed documentation.  Here are some simple examples
of their typical use-cases.

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

#### Get a YAML Value

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

Expand and exclude unwanted results:

```shell
yaml-paths \
  --search=^another \
  --search=$word \
  --except=%bad \
  /some/directory/*.yaml
```

#### Change a YAML Value

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
yaml_data = get_yaml_data(yaml, log, yaml_file)
if yaml_data is None:
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
    for node in processor.get_nodes(yaml_path):
        log.debug("Got {} from '{}'.".format(node, yaml_path))
        # Do something with each node...
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
