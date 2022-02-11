import aiohttp
import aiofiles
import asyncio
import json
import requests
import sys
import wave

from functools import partial, wraps
from pydub import AudioSegment
from vosk import KaldiRecognizer, SetLogLevel

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

SetLogLevel(-1)

def threaded(func):
    @wraps(func)
    async def wrap(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))
    return wrap

def mp3_to_wav(mp3_filename):
    wav_filename = mp3_filename.replace(".mp3", ".wav")
    segment = AudioSegment.from_mp3(mp3_filename)
    sound = segment.set_channels(1).set_frame_rate(16000)
    sound.export(wav_filename, format="wav")
    return wav_filename

@threaded
def get_text(mp3_filename, model):
    wav_filename = mp3_to_wav(mp3_filename)
    wf = wave.open(wav_filename, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        rec.AcceptWaveform(data)
    return json.loads(rec.FinalResult())

async def save_file(file, data, binary=False):
    mode = "w" if not binary else "wb"
    async with aiofiles.open(file, mode=mode) as f:
        await f.write(data)

async def load_file(file, binary=False):
    mode = "r" if not binary else "rb"
    async with aiofiles.open(file, mode=mode) as f:
        return await f.read()

@threaded
def get_page_win(
        url,
        proxy=None,
        proxy_auth=None,
        binary=False,
        timeout=300):
    proxies = None
    if proxy:
        if proxy_auth:
            proxy = proxy.replace("http://", "")
            username = proxy_auth['username']
            password = proxy_auth['password']
            proxies = {
                "http": f"http://{username}:{password}@{proxy}",
                "https": f"http://{username}:{password}@{proxy}"}
        else:
            proxies = {"http": proxy, "https": proxy}
    with requests.Session() as session:
        response = session.get(
            url,
            proxies=proxies,
            timeout=timeout)
        if binary:
            return response.content
        return response.text


async def get_page(
        url,
        proxy=None,
        proxy_auth=None,
        binary=False,
        timeout=300):
    if sys.platform == "win32":
        # SSL Doesn't work on aiohttp through ProactorLoop so we use Requests
        return await get_page_win(
            url, proxy, proxy_auth, binary, verify, timeout)
    else:
        if proxy_auth:
            proxy_auth = aiohttp.BasicAuth(
                proxy_auth['username'], proxy_auth['password'])
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url,
                    proxy=proxy,
                    proxy_auth=proxy_auth,
                    timeout=timeout) as response:
                if binary:
                    return await response.read()
                return await response.text()