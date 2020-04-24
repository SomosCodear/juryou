from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as readme:
    long_description = readme.read()

# get install requirements from requirements.txt file
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as requirements:
    install_requires = [
        line.strip()
        for line in requirements.readlines()
        if not line.startswith('#')
    ]

# get test requirements from requirements-test.txt file
with open(path.join(here, 'requirements-test.txt'), encoding='utf-8') as requirements:
    tests_require = [
        line.strip()
        for line in requirements.readlines()
        if not line.startswith('#')
    ]

setup(
    name='juryou',
    version='0.3.1',
    description='Simple receipt generation library',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/SomosCodear/juryou',
    author='codear',
    author_email='desarrollo@codear.org',
    include_package_data=True,
    packages=find_packages(),
    python_requires='>=3.7',
    install_requires=install_requires,
    test_suite='juryou.tests',
    tests_require=tests_require,
    entry_points={
        'console_scripts': [
            'juryou=juryou.cli:main',
        ],
    },
)
