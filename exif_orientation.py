# Copyright (C) 2013 by Brendan Cox

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
from PIL.ExifTags import TAGS
from PIL import Image

ORIENTATION_TAG = 274

def correct_image_orientation(img):
    exif_dict = img._getexif()
    if exif_dict:
        try:
            orientation = exif_dict[ORIENTATION_TAG]
            if orientation == 3:
                # rotate 180 degrees
                return img.rotate(180)
            elif orientation == 6:
                # rotate 90 degrees clockwise
                return img.rotate(270)
            elif orientation == 8:
                # rotate 90 degrees counterclockwise
                return img.rotate(90)
            return img
        except KeyError:
            # couldn't find exif data
            return img
    else:
        return img

