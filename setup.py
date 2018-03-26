from distutils.core import setup

with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()[1:]

setup(
    name='STB_Liga_export',
    version='1.0',
    author='U2328 and iconstrife',
    package_dir={
        'STB_Liga_export': 'src',
        'misclib': 'src/lib',
    },
    packages=['STB_Liga_export', 'misclib'],

    install_requires=requirements,
)
