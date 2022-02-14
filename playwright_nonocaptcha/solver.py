#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import os
import shutil
import tempfile
import time

import playwright_nonocaptcha.utils as utils
import playwright_nonocaptcha.image as image

from playwright.async_api import async_playwright, TimeoutError
from playwright_stealth import stealth_async
from urllib.parse import urlparse
from vosk import Model


class Solver(object):

    def __init__(self,
        pageurl,
        sitekey,
        proxy=None,
        headless=False,
        timeout=30*1000,
        model=Model('model'),
        net=cv2.dnn.readNet("model/yolov3.weights", "model/yolov3.cfg"),
        solve_by_image=True,
        solve_by_audio=False,):
        self.pageurl = pageurl
        self.sitekey = sitekey
        self.proxy = proxy
        self.headless = headless
        self.timeout = timeout
        self.model = model
        self.net = net
        self.solve_by_image = solve_by_image
        self.solve_by_audio = solve_by_audio
    
    async def start(self):
        self.browser = await self.get_browser()
        self.page = await self.new_page()
        await self.apply_stealth()
        await self.reroute_requests()
        await self.goto_page()
        await self.get_frames()
        await self.click_checkbox()
        result = await self.check_detection(timeout=5)
        if result:
            return await self.get_recaptcha_response()
        if self.solve_by_image:
            result = await self.solve_image()
        else:
            result = await self.solve_audio()
        await self.cleanup()
        if result:
            return result

    async def get_browser(self):
        playwright = await async_playwright().start()
        if self.proxy:
            self.proxy = {'server': self.proxy}
        browser = await playwright.webkit.launch(
            headless=self.headless,
            proxy=self.proxy,
        )
        return browser
    
    async def new_page(self):
        page = await self.browser.new_page()
        page.set_default_timeout(self.timeout)
        return page

    async def apply_stealth(self):
        await stealth_async(self.page)

    async def reroute_requests(self):
        parsed_url = urlparse(self.pageurl)
        scheme = parsed_url.scheme
        netloc = parsed_url.netloc
        await self.page.route(f"{scheme}://{netloc}/*", lambda route: 
            route.fulfill(
            content_type="text/html",
            body=f"<script src=https://www.google.com/recaptcha/api.js?hl=en><"
                 "/script>"
                 f"<div class=g-recaptcha data-sitekey={self.sitekey}></div>")
        )

    async def goto_page(self):
        await self.page.goto(self.pageurl,wait_until="commit")
        await self.page.wait_for_load_state("load")

    async def click_checkbox(self):
        checkbox = await self.checkbox_frame.wait_for_selector(
            "#recaptcha-anchor")
        await checkbox.click()

    async def get_frames(self):
        await self.page.wait_for_selector("iframe[src*=\"api2/anchor\"]",
            state='attached')
        self.checkbox_frame = next(frame for frame in self.page.frames 
            if "api2/anchor" in frame.url)
        await self.page.wait_for_selector("iframe[src*=\"api2/bframe\"]",
            state='attached')
        self.image_frame = next(frame for frame in self.page.frames 
            if "api2/bframe" in frame.url)

    async def click_audio_button(self):
        audio_button = await self.image_frame.wait_for_selector("#recaptcha-au"
            "dio-button")
        await audio_button.click()

    async def check_detection(self, timeout):
        timeout = time.time() + timeout
        while time.time() < timeout:
            content = await self.image_frame.content()
            if 'Try again later' in content:
                return 'detected'
            elif 'Press PLAY to listen' in content:
                return 'solve'
            else:
                result = await self.page.evaluate('document.getElementById("g-'
                    'recaptcha-response").value !== ""')
                if result:
                    return result

    async def solve_audio(self):
        await self.click_audio_button()
        while 1:
            if result == 'solve':
                play_button = await self.image_frame.wait_for_selector("#audio-source",
                    state="attached")
                audio_source = await play_button.evaluate("node => node.src")
                audio_data = await utils.get_page(audio_source, binary=True)
                tmpd = tempfile.mkdtemp()
                tmpf = os.path.join(tmpd, "audio.mp3")
                await utils.save_file(tmpf, data=audio_data, binary=True)
                audio_response = await utils.get_text(tmpf)
                audio_response_input = await self.image_frame.wait_for_selector("#audi"
                    "o-response", state="attached")
                await audio_response_input.fill(audio_response['text'])
                recaptcha_verify_button = await self.image_frame.wait_for_selector("#r"
                    "ecaptcha-verify-button", state="attached")
                await recaptcha_verify_button.click()
                shutil.rmtree(tmpd)
                result = await self.get_recaptcha_response()
                if result:
                    return result
            else:
                break

    async def solve_image(self):
        im = image.SolveImage(self.page, self.image_frame, net=self.net)
        await im.solve_by_image()
        result = await self.get_recaptcha_response()
        if result:
            return result

    async def get_recaptcha_response(self):
        if await self.page.evaluate('document.getElementById("g-recaptcha-resp'
            'onse").value !== ""'):
            recaptcha_response = await self.page.evaluate('document.getElementById'
                '("g-recaptcha-response").value')
            return recaptcha_response

    async def cleanup(self):
        await self.browser.close()
