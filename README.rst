.. image:: https://img.shields.io/pypi/v/playwright-nonocaptcha.svg
    :alt: PyPI
    :target: https://pypi.org/project/playwright-nonocaptcha/
.. image:: https://img.shields.io/pypi/pyversions/playwright-nonocaptcha.svg
    :alt: PyPI - Python Version
    :target: https://pypi.org/project/playwright-nonocaptcha/
.. image:: https://img.shields.io/pypi/l/playwright-nonocaptcha.svg
    :alt: PyPI - License   
    :target: https://pypi.org/project/playwright-nonocaptcha/
.. image:: https://img.shields.io/pypi/status/playwright-nonocaptcha.svg
    :alt: PyPI - Status
    :target: https://pypi.org/project/playwright-nonocaptcha/

Playwright nonoCAPTCHA
===========

An async Python library to automate solving ReCAPTCHA v2 by audio using
Playwright.

Disclaimer
----------

This project is for educational and research purposes only. Any actions
and/or activities related to the material contained on this GitHub
Repository is solely your responsibility. The misuse of the information
in this GitHub Repository can result in criminal charges brought against
the persons in question. The author will not be held responsible in the
event any criminal charges be brought against any individuals misusing
the information in this GitHub Repository to break the law.

Compatibility
-------------

Linux, macOS, and Windows!

Installation
------------

.. code:: shell

   $ pip install playwright-nonocaptcha

Usage
-----

If you want to use it in your own script

.. code:: python

     import asyncio
     import sys

     from playwright_nonocaptcha.solver import Solver

     if len(sys.argv) == 4:
          pageurl, sitekey, proxy = sys.argv[1:]
     else:
          print('Invalid number of arguments (pageurl, sitekey, proxy)')
          sys.exit(0)

     if proxy.lower() == "none":
          proxy = None

     client = Solver(pageurl, sitekey, proxy=proxy)
     result = asyncio.run(client.start())
     if result:
          print(result)
