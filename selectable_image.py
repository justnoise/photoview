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
from Tkinter import *
from PIL import Image, ImageTk
import time
import logging

thumbnail_size = (150, 150)
thumbnail_padding = 5
double_click_threshold = .5
double_click_threshold_ms = int(double_click_threshold * 1000)
selection_box_fill = ('white', 'black')


class SelectableImage(object):
    def __init__(self, canvas, image_path, tk_image):
        self.canvas = canvas
        self.image_path = image_path
        self.tk_image = tk_image
        self.selected = False

        self.single_clicked = False
        self.single_click_callback = None
        self.shift_click_callback = None
        self.double_click_callback = None

    def draw(self, center_x, center_y):
        width = self.tk_image.width()
        height = self.tk_image.height()
        rect_left = center_x - (width/2) - thumbnail_padding
        rect_right = center_x + (width/2) + thumbnail_padding
        rect_top = center_y - (height/2) - thumbnail_padding
        rect_bottom = center_y + (height/2) + thumbnail_padding
        c = selection_box_fill[self.selected]
        self.rect_id = self.canvas.create_rectangle(rect_left, rect_top, 
                                                    rect_right, rect_bottom, 
                                                    fill=c, outline=c)
        self.image_id = self.canvas.create_image(center_x, center_y, image = self.tk_image)

        self.canvas.tag_bind(self.image_id, '<Button-1>', self.single_click)

        self.canvas.tag_bind(self.image_id, '<Double-Button-1>', self.double_click)
        self.canvas.tag_bind(self.image_id, '<Shift-Button-1>', self.shift_click)

    def erase(self):
        self.canvas.delete(self.rect_id)
        self.canvas.delete(self.image_id)

    def draw_selection(self):
        c = selection_box_fill[self.selected]
        image = self.canvas.itemconfig(self.rect_id, fill=c, outline=c)

    def toggle_selection(self):
        self.selected = not bool(self.selected)
        self.draw_selection()

    def shift_click(self, event):
        if self.shift_click_callback:
            self.shift_click_callback(self)

    def single_click(self, event):
        def image_clicked():
            if self.single_clicked:
                logging.debug('from image: single clicked from: ' + str(self.image_path))
                self.toggle_selection()
                if self.single_click_callback:
                    self.single_click_callback(self)
        self.single_clicked = True
        self.recent_click_time = time.time()
        if self.double_click_callback:
            self.canvas.after(double_click_threshold_ms, image_clicked)
        else:
            image_clicked()

    def double_click(self, event):
        logging.debug('saw double click')
        current_click_time = time.time()
        if current_click_time - self.recent_click_time < double_click_threshold:
            self.single_clicked = False
        if self.double_click_callback:
            self.double_click_callback(self)
        else:
            logging.info('no double click callback for this button')
