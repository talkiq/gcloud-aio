import os

import setuptools


PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(PACKAGE_ROOT, 'README.rst')) as f:
    README = f.read()

with open(os.path.join(PACKAGE_ROOT, 'requirements.txt')) as f:
    REQUIREMENTS = [r.strip() for r in f.readlines()]


setuptools.setup(
    name='gcloud-aio-auth',
    version='3.4.4',
    description='Python Client for Google Cloud Auth',
    long_description=README,
    namespace_packages=[
        'gcloud',
        'gcloud.aio',
    ],
    packages=setuptools.find_packages(exclude=('tests',)),
    install_requires=REQUIREMENTS,
    python_requires='>= 3.6',
    author='Vi Engineering',
    author_email='voiceai-eng@dialpad.com',
    url='https://github.com/talkiq/gcloud-aio',
    platforms='Posix; MacOS X; Windows',
    include_package_data=True,
    zip_safe=False,
    license='MIT License',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Internet',
    ],
)
