# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
    name='mittepro',
    version='2.0.0',
    install_requires=[
        'requests==2.21.0',
        'simplejson==3.16.0',
        'apysignature==0.2.1',
    ],
    url='https://github.com/ThCC/mittepro-py',
    description='MittePro is a powerful marketing tool with features to help companies with their marketing goals and deliver emails from their websites and apps.',
    long_description=open("README.rst").read(),
    packages=find_packages(),
    include_package_data=True,
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    license='Apache-2.0',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries',
    ],
    author='Thiago Cardoso de Castro',
    author_email='thiago.decastro2@gmail.com',
)

# python setup.py sdist bdist_wheel
# twine upload dist/mittepro-x.y.z.tar.gz
# twine upload dist/mittepro-x.y.z-py2-none-any.whl
