from setuptools import setup, find_packages

setup(
    name='PGPass',
    version='0.2.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click>=7.1.2',
        'python-gnupg>=0.4.6',
        'pyperclip>=1.8.0',
        'click-shell>=2.0',
        'pyyaml>=5.3.1',
        'colorama>=0.4.3',
    ],
    entry_points={
        'console_scripts': ['pgpass = PGPass.__main__:cli'],
    },
    author='fitebone',
    description='This is a CLI to manage a password store with gnupg',
)
