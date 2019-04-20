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
            "anime-planet-downloader=animeu.spiders.anime_planet_downloader:main",
            "anime-planet-extractor=animeu.spiders.anime_planet_extractor:main",
            "myanimelist-downloader=animeu.spiders.myanimelist_downloader:main",
            "myanimelist-extractor=animeu.spiders.myanimelist_extractor:main",
            "merge-json=animeu.spiders.json_helpers:merge_json_files_cli"
        ]
    },
    install_requires=["Flask"]
)
