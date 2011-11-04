import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'colander',
    'deform',
    'pyramid',
    'pyramid_tm',
    'pyramid_debugtoolbar',
    'requests',
    'sqlalchemy',
    'zope.sqlalchemy',
]

if sys.version_info[:3] < (2, 5, 0):
    requires.append('pysqlite')

setup(
    name='microbank',
    version='0.0',
    description='microbank',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
          "Programming Language :: Python",
          "Framework :: Pylons",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author='Shane Hathaway',
    author_email='shane@wingcash.com',
    url='http://shane.willowrise.com',
    keywords='web pylons pyramid',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    tests_require=requires,
    test_suite="microbank",
    entry_points="""\
    [paste.app_factory]
    main = microbank:main
    """,
    # paster_plugins=['pyramid'],
)
