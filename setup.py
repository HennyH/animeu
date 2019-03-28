from setuptools import setup, find_packages

setup(
    name="animeu",
    verison="0.0.1",
    long_description=__doc__,
    packages=find_packages(
        exclude=("build", "node_modules", "static", "templates")
    ),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "Flask",
        "Flask-Webpack"
    ]
)
