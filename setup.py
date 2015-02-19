import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

import artexin


with open("README.rst") as readme_file:
    README = readme_file.read()

install_requires = [
    'beautifulsoup4',
    'breadability',
    'nltk',
    'Pillow',
    'python-gnupg',
    'selenium',
    'simplejson'
]


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = [artexin.__name__, '--doctest-modules']

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(name='artexin',
      version=artexin.__version__,
      packages=find_packages(),
      description="ArtExIn - Article Extraction and Indexing",
      long_description=README,
      include_package_data=True,
      zip_safe=False,
      classifiers=[
          "Programming Language :: Python",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4",
          "Development Status :: 3 - Alpha"
      ],
      install_requires=install_requires,
      tests_require=['pytest'],
      cmdclass={'test': PyTest})
