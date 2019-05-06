from setuptools import setup

setup(
    name="yamlpath",
    version="1.0.0",
    description="Generally-useful YAML and EYAML tools that implement YAML Path",
    long_description="This project presents and utilizes YAML Paths, which are"
        + " a human-friendly means of expressing a path through the structure"
        + " of YAML data to a specific key or a set of keys matching some"
        + " search criteria.",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    url="https://github.com/wwkimball/yamlpath",
    author="William W. Kimball, Jr., MBA, MSIS",
    author_email="github-yamlpath@kimballstuff.com",
    license="ISC",
    keywords="yaml eyaml",
    packages=["yamlpath"],
    scripts=[
        "bin/eyaml-rotate-keys",
        "bin/yaml-get",
        "bin/yaml-set",
    ],
    install_requires=[
        "ruamel.yaml",
    ],
    tests_require=["pytest"],
    include_package_data=True,
    zip_safe=False
)