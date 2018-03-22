from distutils.core import setup

with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()[1:]

setup(
    name='STB-Liga-export',
    version='1.0',
    author='U2328 and iconstrife',
    package_dir={
        'STB-Liga-export': 'src',
        'misclib': 'src/lib',
    },
    packages=['STB-Liga-export', 'misclib'],
    entry_points={
        'console_scripts': ['STB_Liga=src.main:main'],
    },
    install_requires=requirements,
)
