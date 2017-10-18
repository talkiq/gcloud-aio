import os

import setuptools


PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(PACKAGE_ROOT, 'README.rst')) as f:
    README = f.read()


REQUIREMENTS = [
    'gcloud-aio-taskqueue >= 0.0.0, < 1.0.0',
]


setuptools.setup(
    name='gcloud-aio',
    version='0.0.0',
    description='Asyncio API Client library for Google Cloud',
    long_description=README,
    install_requires=REQUIREMENTS,
    author='Jonathan Dobson',
    author_email='jon.m.dobson@gmail.com',
    url='https://github.com/jomido/gcloud-aio',
    platforms='Posix; MacOS X; Windows',
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet',
    ],
)
