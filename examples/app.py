#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys

from aiohttp import web
from urllib.parse import unquote

from solverecaptchas.solver import Solver
from vosk import Model, KaldiRecognizer, SetLogLevel

model = Model("model")

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
        headless=headless,
        model=model
    )
    result = await client.start()
    if result:
        return result

async def get_solution(request):
    params = request.rel_url.query
    pageurl = params.get("pageurl")
    sitekey = params.get("sitekey")
    proxy = params.get("proxy")
    if proxy:
        proxy = unquote(proxy)
    timeout = 300*1000
    if not pageurl or not sitekey:
        response = {"error": "invalid request"}
    else:
        result = None
        while not result:
            result = await work(
                unquote(pageurl), sitekey, timeout=timeout, proxy=proxy, headless=False)
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
    web.run_app(app())
