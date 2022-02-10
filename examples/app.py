#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Threaded example using executor to create a new event loop for running a
task. Each task will continue to retry solving until it succeeds or times-out
per the specified duration. Default is 180 seconds (3 minutes). On shutdown
cleanup will propagate, hopefully closing left-over browsers and removing
temporary profile folders.
"""

import argparse
import asyncio
import shutil
import sys

from aiohttp import web

from playwright_nonocaptcha.solver import Solver

if sys.platform == "win32":
    parent_loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(parent_loop)
else:
    parent_loop = asyncio.get_event_loop()
    asyncio.get_child_watcher().attach_loop(parent_loop)

app = web.Application()

async def work(pageurl, sitekey, timeout, proxy, headless):
    client = Solver(
        pageurl,
        sitekey,
        timeout=timeout,
        proxy=proxy,
        headless=headless
    )
    result = await client.start()
    if result:
        return result

async def get_solution(request):
    params = request.rel_url.query
    pageurl = params.get("pageurl")
    sitekey = params.get("sitekey")
    proxy = params.get("proxy")
    timeout = 300*1000
    if not pageurl or not sitekey:
        response = {"error": "invalid request"}
    else:
        result = None
        while not result:
            result = await work(
                pageurl, sitekey, timeout=timeout, proxy=proxy, headless=True)
            if result:
                response = {"solution": result}
            else:
                response = {"error": "worker timed-out"}
    return web.json_response(response)

async def cleanup_background_tasks(app):
    app["dispatch"].cancel()
    await app["dispatch"]

async def app():
    app = web.Application()
    app.router.add_get('/', get_solution)
    return app

if __name__ == "__main__":
    args = parser.parse_args()
    web.run_app(app, path=args.path, port=args.port)
