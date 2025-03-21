from setuptools import setup, find_namespace_packages

setup(
    name='penquest-pkgs',
    version='0.2.2',
    description='Holds common models, constants, etc. of the PenQuest project',
    author='Sebastian Eresheim, Alexander Piglmann, Simon Gmeiner, Thomas Petelin',
    author_email="sebastian.eresheim@fhstp.a.at",
    license="MIT Licsense",
    packages=find_namespace_packages(exclude=['dist*']),
    install_requires=[
        "asyncio>=3.4.3",
        "numpy>=2.2.2",
        "pandas>=2.2.3",
    ],
    classifiers=[""]
)