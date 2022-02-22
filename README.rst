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
=======================

An async Python library to automate solving ReCAPTCHA v2 using
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

Trained model
----------------
I've trained a model that detects each of the following classes which support 9x grid.

1. bicycle
2. boat
3. bridge
4. bus
5. car
6. chimneys
7. crosswalk
8. fire hydrant
9. motorcycles
10. mountains or hills
11. palm trees
12. stair
13. taxi
14. tow truck
15. traffic light
16. traffic sign
17. truck

This model can be downloaded from https://mikey.id/yolov3.weights. I've provided the other necessary files under **model/**.

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
