"""Installs logmerger and prints help text with Python 3.9 - 3.12

Use this file with the `nox` tool to run logmerger with all specified versions
of Python. For more information, see: https://nox.thea.codes/en/stable/

TODO: Find a way to verify that logmerger/about.py and README.md have been updated
to match CLI options, so the test is more than a simple "smoke test" like it is now.
"""
import nox

@nox.session(python=["3.9", "3.10", "3.11", "3.12", "3.13"])
def smoke_test(session):
    session.install(".")
    session.run("logmerger", "-h")
