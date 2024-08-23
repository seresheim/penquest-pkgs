from setuptools import setup, find_namespace_packages

setup(
    name='penquest-pkgs',
    version='0.1.0',
    description='Holds common models, constants, etc. of the PenQuest project',
    author='Sebastian Eresheim, Alexander Piglmann, Simon Gmeiner, Thomas Petelin',
    author_email="sebastian.eresheim@fhstp.a.at",
    license="",
    packages=find_namespace_packages(exclude=['dist*']),
    install_requires=[
        "asyncio>=3.4.3"
    ],
    classifiers=[""]
)