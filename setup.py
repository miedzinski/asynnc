from setuptools import find_packages, setup

setup(
    name='nnc',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'nnc=nnc.main:main'
        ],
    },
)
