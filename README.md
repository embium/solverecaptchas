I've decided to introduce this project as a single file on it's first commit to keep it simple enough for beginners to understand.

It's a very simple script demonstrating how to solve reCAPTCHA v2's audio section using Playwright.

This project is a work in progress and will continue to receive updates until it's ready for production use.

Many things aren't taken into consideration yet, such as when you are required to solve another time, if you've sent too many requests and lack of proxy support - which will all be implemented at a later date.

Contributions are more than welcomed.

Heavily inspired by [nonoCAPTCHA](https://github.com/mikeyy/nonoCAPTCHA), where I was the original maintainer.

## Installation 
Tested under Ubuntu 20.04. It should work under Windows as well.
- git clone https://github.com/embium/recaptcha-solver
- pip install -r requirements.txt
- playwright install
- playwright install-deps

## How to run
- python solve.py https://recaptcha-demo.appspot.com/recaptcha-v2-checkbox.php 6LfW6wATAAAAAHLqO2pb8bDBahxlMxNdo9g947u9

Really, it's as simple as that. 