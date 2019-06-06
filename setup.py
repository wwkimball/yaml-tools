import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="yamlpath",
    version="2.1.0",
    description="Read and change YAML/Compatible data using powerful, intuitive, command-line friendly syntax",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    url="https://github.com/wwkimball/yamlpath",
    author="William W. Kimball, Jr., MBA, MSIS",
    author_email="github-yamlpath@kimballstuff.com",
    license="ISC",
    keywords="yaml eyaml yaml-path",
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": [
            "eyaml-rotate-keys = yamlpath.commands.eyaml_rotate_keys:main",
            "yaml-get = yamlpath.commands.yaml_get:main",
            "yaml-paths = yamlpath.commands.yaml_paths:main",
            "yaml-set = yamlpath.commands.yaml_set:main",
        ]
    },
    python_requires=">3.6.0",
    install_requires=[
        "ruamel.yaml>=0.15.96",
    ],
    tests_require=[
        "pytest",
        "pytest-cov",
        "pytest-console-scripts",
    ],
    include_package_data=True,
    zip_safe=False
)
