import os
import time
import requests
from PIL import Image
from io import BytesIO
from skimage import io
import numpy as np

# Updated GoogleMaps class from deprecated Python2 to Python3 by manas-1404. Original work by Adrian Albert

class GoogleMaps:
    """ Lightweight wrapper class for the Google Maps API. """
    def __init__(self, key=None):
        self._key = key

    def construct_static_url(self, latlon, zoom=17, imgsize=(500,500),
                             maptype="roadmap", imgformat="jpeg"):
        center = "{:.5f},{:.5f}".format(*latlon) if isinstance(latlon, tuple) else latlon
        return self.construct_googlemaps_url_request(
            center=center,
            zoom=zoom,
            imgsize=imgsize,
            maptype=maptype,
            imgformat=imgformat,
            apiKey=self._key)

    def get_static_map_image(self, request, max_tries=2, filename=None, crop=False):
        num_tries = 0
        while num_tries < max_tries:
            num_tries += 1
            img = self.get_static_google_map(request, filename=filename, crop=crop)
            if img is not None:
                return img
            print("Error! Trying again ({}/{}) in 5 sec".format(num_tries, max_tries))
            time.sleep(5)
        return None

    @staticmethod
    def construct_googlemaps_url_request(center=None, zoom=None, imgsize=(500,500),
                                         maptype="roadmap", apiKey="", imgformat="jpeg"):
        request = "http://maps.google.com/maps/api/staticmap?"  # base URL, append query params, separated by &
        if center:
            request += "center={}&".format(center.replace(" ", "+"))
        if zoom is not None:
            request += "zoom={}&".format(zoom)
        if apiKey:
            request += "key={}&".format(apiKey)
        request += "size={}x{}&format={}&maptype={}&sensor=false".format(*imgsize, imgformat, maptype)
        return request

    @staticmethod
    def get_static_google_map(request, filename=None, crop=False):
        response = requests.get(request)

        print("Response: ", response)

        if 'x-staticmap-api-warning' in response.headers:
            return None

        try:
            img = Image.open(BytesIO(response.content))
        except IOError:
            print("IOError: Error in loading image")
            return None
        else:
            img = np.array(img.convert("RGB"))

        # Hack to check for the Google API limit error image
        if (img == 224).sum() / float(img.size) > 0.95:
            return None

        # Optionally remove the Google watermark
        if crop:
            img_shape = img.shape
            img = img[:int(img_shape[0] * 0.85), :int(img_shape[1] * 0.85)]

        if filename:
            basedir = os.path.dirname(filename)
            if not os.path.exists(basedir) and basedir not in ["", "./"]:
                os.makedirs(basedir)
            io.imsave(filename, img)

        return img
    