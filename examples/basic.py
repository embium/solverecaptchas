import asyncio
import sys

from solverecaptchas.solver import Solver

if len(sys.argv) == 4:
    pageurl, sitekey, proxy = sys.argv[1:]
else:
    print('Invalid number of arguments (pageurl, sitekey, proxy)')
    sys.exit(0)

if proxy.lower() == "none":
    proxy = None


try:
    client = Solver(pageurl, sitekey, proxy=proxy, headless=False)
    result = asyncio.run(client.start())
    if result:
        print(result)
except Exception as e:
    print(e)