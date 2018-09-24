from setuptools import find_packages, setup


def read_requirements():
    with open('requirements.txt') as f:
        return f.read().splitlines()


setup(
    name='nnc',
    packages=find_packages(),
    install_requires=read_requirements(),
    entry_points={
        'console_scripts': [
            'nnc=nnc.main:main'
        ],
    },
)
