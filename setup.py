import os

import setuptools


PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(PACKAGE_ROOT, 'README.rst')) as f:
    README = f.read()


REQUIREMENTS = [
    'gcloud-aio-auth >= 0.5.0, < 1.0.0',
    'gcloud-aio-bigquery >= 0.5.0, < 1.0.0',
    'gcloud-aio-core >= 0.5.0, < 1.0.0',
    'gcloud-aio-pubsub >= 0.5.0, < 1.0.0',
    'gcloud-aio-storage >= 0.5.0, < 1.0.0',
    'gcloud-aio-taskqueue >= 0.5.0, < 1.0.0',
]


setuptools.setup(
    name='gcloud-aio',
    version='0.5.1',  # TODO: figure out the Right Way™ to version this
    description='Asyncio Client library for Google Cloud API',
    long_description=README,
    install_requires=REQUIREMENTS,
    author='TalkIQ',
    author_email='engineering@talkiq.com',
    url='https://github.com/talkiq/gcloud-aio',
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
