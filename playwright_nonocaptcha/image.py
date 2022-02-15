#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Image solving module. """
import asyncio
import os
import time

from PIL import Image

from playwright_nonocaptcha import package_dir
import playwright_nonocaptcha.utils as utils


class SolveImage():
    title = None
    pieces = None
    download = None
    cur_image_path = None

    def __init__(self, page, image_frame, net, proxy=None, proxy_auth=None, **kwargs):
        self.page = page
        self.image_frame = image_frame
        self.net = net
        self.proxy=proxy
        self.proxy_auth=proxy_auth

    async def get_start_data(self):
        """Detect pieces and get title image"""
        await self.get_title()
        image = await self.download_image()
        await self.create_folder(self.title, image)
        file_path = os.path.join(self.cur_image_path, f'{self.title}.jpg')
        await utils.save_file(file_path, image, binary=True)
        self.pieces = await self.image_no()
        return file_path

    async def solve_by_image(self):
        """Go through procedures to solve image"""
        while True:
            file_path = await self.get_start_data()
            unsolvable = [
                'chimneys',
                'stair',
                'crosswalk',
                'mountains_or_hills',
                'tractors',
                'palm_trees'
            ]
            if self.title in unsolvable:
                await self.click_reload_button()
                if not await self.is_next() and not await self.is_finish():
                    continue
            choices = await self.choose(file_path)
            await self.click_image(choices)
            if self.pieces == 16:
                await self.click_verify()
            elif self.pieces == 9:
                if choices:
                    if await self.is_one_selected():
                        await self.cycle_selected(choices)
                        await self.click_verify()
                        if not await self.is_next() and not await self.is_finish():
                            await self.click_reload_button()
                    else:
                        await self.click_verify()
                        if not await self.is_next() and not await self.is_finish():
                            await self.click_reload_button()
                else:
                    await self.click_reload_button()
            result = await self.check_detection(5)
            if result:
                break


    async def cycle_selected(self, selected):
        """Cyclic image selector"""
        while True:
            await self.check_detection(5)
            images = await self.get_images_block(selected)
            new_selected = []
            i = 0
            for image_url in images:
                if images != self.download:
                    image = await utils.get_page(
                        image_url, self.proxy, self.proxy_auth, binary=True
                    )
                    await self.create_folder(self.title, image)
                    file_path = os.path.join(
                        self.cur_image_path, f'{self.title}.jpg')
                    await utils.save_file(file_path, image, binary=True)

                    result = self.net.predict(file_path)
                    if self.title == 'vehicles':
                        if 'car' in result or 'truck' in result:
                            new_selected.append(selected[i])
                    if (self.title != 'vehicles' 
                            and self.title.replace('_', ' ') in result):
                        new_selected.append(selected[i])
                i += 1
            if new_selected:
                await self.click_image(new_selected)
            else:
                break

    async def click_verify(self):
        await self.image_frame.locator('#recaptcha-verify-button').click()

    async def click_reload_button(self):
        await self.image_frame.locator("#recaptcha-reload-button").click()

    async def choose(self, image_path):
        """Get list of images selected"""
        selected = []
        if self.pieces == 9:
            image_obj = Image.open(image_path)
            utils.split_image(image_obj, self.pieces, self.cur_image_path)
            for i in range(self.pieces):
                result = self.net.predict(os.path.join(self.cur_image_path, f'{i}.jpg'))
                print(result)
                if self.title.replace('_', ' ') in result:
                    selected.append(i)
        else:
            result = self.net.predict(image_path, self.title.replace('_', ' '))
            if result is not False:
                image_obj = Image.open(result)
                utils.split_image(image_obj, self.pieces, self.cur_image_path)
                for i in range(self.pieces-1):
                    if self.net.is_marked(f"{self.cur_image_path}/{i}.jpg"):
                        selected.append(i)
                # os.remove(result)
        return selected

    async def get_images(self):
        """Get list of images"""
        table = self.image_frame.locator('table')
        rows = table.locator('tr')
        count = await rows.count()
        for i in range(count):
            cells = rows.nth(i).locator('td')
            count = await cells.count()
            for i in range(count):
                yield cells.nth(i)

    async def click_image(self, list_id):
        """Click specific images of the list"""
        elements = self.image_frame.locator('.rc-imageselect-tile')
        for i in list_id:
            await elements.nth(i).click()

    async def search_title(self, title):
        """Search title with classes"""
        classes = ('bus', 'car', 'bicycle', 'fire_hydrant', 'crosswalk', 'stair', 'bridge', 'traffic_light',
                   'vehicles', 'motorbike', 'boat', 'chimneys')
        # Only English and Spanish detected!
        possible_titles = (
            ('autobuses', 'autobús', 'bus', 'buses'),
            ('automóviles', 'cars', 'car', 'coches', 'coche'),
            ('bicicletas', 'bicycles', 'bicycle', 'bici'),
            ('boca de incendios', 'boca_de_incendios', 'una_boca_de_incendios', 'fire_hydrant', 'fire_hydrants',
             'a_fire_hydrant', 'bocas_de_incendios'),
            ('cruces_peatonales', 'crosswalk', 'crosswalks', 'cross_walks', 'cross_walk', 'pasos_de_peatones'),
            ('escaleras', 'stair', 'stairs'),
            ('puentes', 'bridge', 'bridges'),
            ('semaforos', 'semaphore', 'semaphores', 'traffic_lights', 'traffic_light', 'semáforos'),
            ('vehículos', 'vehicles'),
            ('motocicletas', 'motocicleta', 'motorcycle', 'motorcycle', 'motorbike'),
            ('boat', 'boats', 'barcos', 'barco'),
            ('chimeneas', 'chimneys', 'chimney', 'chimenea')
        )
        i = 0
        for objects in possible_titles:
            if title in objects:
                return classes[i]
            i += 1
        return title

    async def pictures_of(self):
        """Get title of solve object"""
        el = await self.get_description_element()
        return str(el).replace(' ', '_')

    async def get_description_element(self):
        """Get text of object"""
        name = self.image_frame.locator('.rc-imageselect-desc-wrapper strong')
        return await name.inner_text()

    async def create_folder(self, title, image):
        """Create tmp folder and save image"""
        if not os.path.exists('pictures'):
            os.mkdir('pictures')
        if not os.path.exists(os.path.join('pictures', f'{title}')):
            os.mkdir(os.path.join('pictures', f'{title}'))
        if not os.path.exists(os.path.join('pictures', 'tmp')):
            os.mkdir(os.path.join('pictures', 'tmp'))
        self.cur_image_path = os.path.join(
            os.path.join('pictures', f'{title}'), f'{hash(image)}')
        if not os.path.exists(self.cur_image_path):
            os.mkdir(self.cur_image_path)

    async def get_image_url(self):
        """Get image url for download"""
        code = (
            'document.getElementsByClassName("rc-image-tile-wrapper")[0].'
            'getElementsByTagName("img")[0].src'
        )
        image_url = await self.image_frame.evaluate(code)
        return image_url

    async def image_no(self):
        """Get number of images in captcha"""
        return len([i async for i in self.get_images()])

    async def is_one_selected(self):
        """Is one selection or multi-selection images"""
        code = (
            'document.getElementsByClassName("rc-imageselect-tileselected").'
            'length === 0'
        )
        ev = await self.image_frame.evaluate(code)
        return ev

    async def is_finish(self):
        """Return true if process is finish"""
        result = await self.check_detection(5)
        if result:
            return True
        return False

    async def is_next(self):
        """Verify if next captcha or the same"""
        image_url = await self.get_image_url()
        return False if image_url == self.download else True

    async def download_image(self):
        """Download image captcha"""
        self.download = await self.get_image_url()
        return await utils.get_page(
            self.download, self.proxy, self.proxy_auth, binary=True)

    async def get_images_block(self, images):
        """Get specific image in the block"""
        images_url = []
        for element in images:
            image_url = (
                'document.getElementsByClassName("rc-image-tile-wrapper")['
                f'{element}].getElementsByTagName("img")[0].src'
            )
            result = await self.image_frame.evaluate(image_url)
            images_url.append(result)
        return images_url

    async def get_title(self):
        """Get title of image to solve"""
        title = await self.pictures_of()
        self.title = await self.search_title(title)

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
