from setuptools import setup

setup(
    name='zlock',
    version='0.0.1',
    url='https://github.com/max0d41/zlock',
    description='A disturbed locking system based on ZRPC.',
    packages=[
        'zlock',
    ],
    install_requires=[
        'azrpc>=1.0.0',
    ],
    dependency_links=[
        'https://github.com/max0d41/azrpc/archive/master.zip#egg=azrpc-1.0.0',
    ],
)
