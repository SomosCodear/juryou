from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='juryou',
    version='0.1.0',
    description='Simple receipt generation library',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/SomosCodear/juryou',
    author='codear',
    author_email='desarrollo@codear.org',
    packages=find_packages(),
    python_requires='>=3.7',
    install_requires=[
        'py3afipws',
        'httplib2',
        'py3simplesoap',
        'pyopenssl',
        'weasyprint',
        'python-barcode',
        'jinja2',
    ],
    test_suite='juryou.tests',
    entry_points={
        'console_scripts': [
            'juryou=juryou.cli:main',
        ],
    },
)
