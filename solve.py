#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import requests
import shutil
import sys
import tempfile
import wave

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import stealth_sync
from pydub import AudioSegment
from urllib.parse import urlparse
from vosk import Model, KaldiRecognizer, SetLogLevel

SetLogLevel(0)

if not os.path.exists("model"):
    print ("Please download the model from https://alphacephei.com/vosk/models and unpack as 'model' in the current folder.")
    exit(1)

def mp3_to_wav(mp3_filename):
    wav_filename = mp3_filename.replace(".mp3", ".wav")
    segment = AudioSegment.from_mp3(mp3_filename)
    sound = segment.set_channels(1).set_frame_rate(16000)
    sound.export(wav_filename, format="wav")
    return wav_filename

def get_text(mp3_filename):
    wav_filename = mp3_to_wav(mp3_filename)
    wf = wave.open(wav_filename, "rb")
    model = Model("model")
    rec = KaldiRecognizer(model, wf.getframerate())
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        rec.AcceptWaveform(data)
    return json.loads(rec.FinalResult())

def save_file(file, data, binary=False):
    mode = "w" if not binary else "wb"
    with open(file, mode) as file:
        file.write(data)

def get_page(
        url,
        binary=False,
        timeout=300):
    with requests.Session() as session:
        response = session.get(
            url,
            timeout=timeout)
        if binary:
            return response.content
        return response.text

def main(pageurl, sitekey):
    # Code we will inject into the page
    widget_code = (f"<script src=https://www.google.com/recaptcha/api.js?hl=en async defer></script>"
                   f"<div class=g-recaptcha data-sitekey={sitekey}>"
                    "</div>")
    parsed_url = urlparse(pageurl)
    scheme = parsed_url.scheme
    netloc = parsed_url.netloc
    with sync_playwright() as p:
        # Launch web browser
        browser = p.webkit.launch(headless=False)
        # Open a new page
        page = browser.new_page()
        # Apply anti-bot stealth
        stealth_sync(page)
        # Hacky - Reroute request from supplied url to a page with only the recaptcha box
        # A better solution may be available but I haven't found one
        page.route(f"{scheme}://{netloc}/*", lambda route: route.fulfill(
            content_type="text/html",
            body=f"{widget_code}")
        )
        # Go to url
        page.goto(pageurl, wait_until='commit')
        # Wait for load state
        page.wait_for_load_state("load")
        # Wait for image frame to be available
        page.wait_for_selector("iframe[src*=\"api2/bframe\"]", state="attached")
        # Get frames
        checkbox_frame = next(frame for frame in page.frames if "api2/anchor" in frame.url)
        image_frame = next(frame for frame in page.frames if "api2/bframe" in frame.url)
        # Wait for checkbox to be visible
        checkbox = checkbox_frame.wait_for_selector("#recaptcha-anchor")
        # Click checkbox
        checkbox.click()
        # Wait for audio button to be visible
        audio_button = image_frame.wait_for_selector('#recaptcha-audio-button')
        # Click audio button
        audio_button.click()
        # Wait for play button
        play_button = image_frame.wait_for_selector("#audio-source", state="attached")
        # Extract audio file's location
        audio_source = play_button.evaluate("node => node.src")
        # Download audio file
        audio_data = get_page(audio_source, binary=True)
        # Create temporary directory for audio file
        tmpd = tempfile.mkdtemp()
        # Save audio file
        tmpf = os.path.join(tmpd, "audio.mp3")
        save_file(tmpf, data=audio_data, binary=True)
        # Speech to text recognition using Vosk
        audio_response =get_text(tmpf)
        # Obtain audio response input field
        audio_response_input = image_frame.wait_for_selector("#audio-response", state="attached")
        # Fill in audio responsed input field
        audio_response_input.fill(audio_response['text'])
        # Obtain recaptcha verify button
        recaptcha_verify_button = image_frame.wait_for_selector("#recaptcha-verify-button", state="attached")
        # Click recaptcha verify button
        recaptcha_verify_button.click()
        # Wait until recaptcha response isn't empty
        page.wait_for_function('document.getElementById("g-recaptcha-response").value !== ""')
        # Extract recaptcha response
        recaptcha_response = page.evaluate('document.getElementById("g-recaptcha-response").value')
        # Close browser
        browser.close()
        # Remove temporary directory
        shutil.rmtree(tmpd)
        # Return recaptcha response
        return recaptcha_response

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('This script requires 2 arguments - (pageurl, sitekey)')
    else:
        pageurl = sys.argv[1]
        sitekey = sys.argv[2]
        response = main(pageurl, sitekey)
        print(response)
