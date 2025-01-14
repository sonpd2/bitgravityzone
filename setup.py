import setuptools

setuptools.setup(
    name="bitgravityzone",
    version="0.0.8",
    author="son",
    author_email="son@example.com",
    description="GravityZone API",
    long_description="GravityZone API https://www.bitdefender.com/business/support/en/77211-125277-public-api.html",
    long_description_content_type="text/markdown",
    url="https://github.com/sonpd2/bitgravityzone",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "httpx>=0.24.0",  # Specify the version of httpx you require
    ],
)
