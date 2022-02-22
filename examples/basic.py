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

while 1:
    try:
        client = Solver(pageurl, sitekey, proxy=proxy, headless=False)
        result = asyncio.run(client.start())
        if result:
            print(result)
    except:
        pass