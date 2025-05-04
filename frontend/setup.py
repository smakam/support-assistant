from setuptools import setup, find_packages

setup(
    name="kgen-support-frontend",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "streamlit==1.26.0",
        "requests==2.31.0",
        "python-dotenv==1.0.0",
        "python-jose==3.3.0",
    ],
) 