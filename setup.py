from setuptools import setup


def long_desc():
    with open('README.rst', 'rb') as f:
        return f.read()

kw = {
    "name": "corrections",
    "version": "0.2.3",
    "description": '',
    "long_description": long_desc(),
    "url": "https://github.com/plausibility/corrections",
    "author": "plausibility",
    "author_email": "chris@gibsonsec.org",
    "license": "MIT",
    "packages": [
        'corrections'
    ],
    "package_dir": {
        "corrections": "corrections"
    },
    "install_requires": [
        "gevent",
        "twitter"
    ],
    "zip_safe": False,
    "keywords": "twitter bot corrections",
    "classifiers": [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2"
    ]
}

if __name__ == "__main__":
    setup(**kw)
