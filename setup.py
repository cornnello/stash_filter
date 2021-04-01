from setuptools import setup

setup(
    name="stash_filter",
    version="0.1",
    py_modules=["stash_filter"],
    install_requires=[
        "Click",
    ],
    entry_points="""
        [console_scripts]
        stash_filter=stash_filter:stash_filter
    """,
)