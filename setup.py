from setuptools import setup, find_packages

setup(
    name="animeu",
    verison="0.0.1",
    long_description=__doc__,
    packages=find_packages("animeu"),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "download-character-pages=animeu.anime_planet.page_downloader:main",
            "extract-character-metadata=animeu.anime_planet.page_extractor:main"
        ]
    },
    install_requires=[
        "Flask",
        "Flask-Webpack"
    ]
)
