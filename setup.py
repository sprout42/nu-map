from setuptools import setup, find_packages
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


DESCRIPTION = read('README.rst')
setup(
    name='numap',
    version='2.0.2',
    description='USB Host Security Assessment Tool - Revision 2',
    long_description=DESCRIPTION,
    author='NCCGroup & Cisco SAS team',
    author_email='',
    url='https://github.com/nccgroup/numap',
    packages=find_packages(),
    install_requires=[
        'six',
        'docopt',
        'kittyfuzzer>=0.6.9',
        'facedancer'
    ],
    keywords='security,usb,fuzzing,kitty',
    entry_points={
        'console_scripts': [
            'numap-detect=numap.apps.detect_os:main',
            'numap-emulate=numap.apps.emulate:main',
            'numap-fuzz=numap.apps.fuzz:main',
            'numap-list=numap.apps.list_classes:main',
            'numap-kitty=numap.fuzz.fuzz_engine:main',
            'numap-scan=numap.apps.scan:main',
            'numap-vsscan=numap.apps.vsscan:main',
            'numap-stages=numap.apps.makestages:main',
        ]
    },
    package_data={}
)
