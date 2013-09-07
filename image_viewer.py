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
import exif_orientation
import logging
import pdb

# if IMAGE_WINDOW_OFFSET isn't an odd number, 
# the window resizes after thumbnail is created.  Awesome, huh?
IMAGE_WINDOW_OFFSET = 99 
MENU_BAR_THICKNESS = 22

# Todo: zoom (command +/-)
# Todo: scroll when zoomed
# Todo, select photo by hitting space in this window

class ImageViewer(object):
    def __init__(self, master, image_path, folder_image_paths = None, create_fullscreen = False):
        self.master = master
        self.image_path = image_path
        self.folder_image_paths = folder_image_paths
        self.create_fullscreen = create_fullscreen
        self.fullscreen_window = None

        self.screen_width = master.winfo_screenwidth()
        self.screen_height = master.winfo_screenheight()
        self.reset_window_width_height()

        self.top = Toplevel(width=int(self.window_width), height=int(self.window_height), bg='black')
        if self.create_fullscreen:
            self.top.geometry('%sx%s+0+%s' % (str(self.screen_width), 
                                              str(self.screen_height - MENU_BAR_THICKNESS), 
                                              str(MENU_BAR_THICKNESS)))
            self.top.overrideredirect(self.create_fullscreen)

        self.load_image()
        self.label = Label(self.top, image=self.image_tk, padx=0, pady=0, bg='black', bd = 0)
        self.label.pack(fill=BOTH, expand=1)
        
        self.label.bind('<Configure>', self.resized)
        self.top.bind('<Control-f>', self.control_f)
        self.top.bind('<Escape>', self.destroy_fullscreen)
        self.top.bind('<Left>', self.previous_image)
        self.top.bind('<Right>', self.next_image)
        # case where Command-w closes rear window when in fullscreen
        self.top.protocol("WM_DELETE_WINDOW", self.close_window)

    def previous_image(self, event):
        self.next_or_previous_image(get_next_image=False)

    def next_image(self, event):
        self.next_or_previous_image(get_next_image=True)

    def next_or_previous_image(self, get_next_image):
        if not self.folder_image_paths:
            return
        i = self.folder_image_paths.index(self.image_path)
        increment = 1 if get_next_image else -1
        i += increment
        if i >= 0 and i < len(self.folder_image_paths):
            self.image_path = self.folder_image_paths[i]
            self.load_image()
            self.draw_image()
            # fullscreen window doesn't get events, the bg window
            # needs to tell it what to do
            if self.fullscreen_window:
                self.fullscreen_window.image_path = self.folder_image_paths[i]
                self.fullscreen_window.load_image()
                self.fullscreen_window.draw_image()        
            
    def close_window(self):
        self.destroy_fullscreen(None)
        self.top.destroy()

    def destroy_fullscreen(self, event):
        # when created fullscreen, the window doesn't respond to events
        # so the creating window will recieve the events and destroy it
        if self.fullscreen_window:
            self.fullscreen_window.top.destroy()
            self.fullscreen_window = None

    def create_fullscreen_window(self):
        if not self.fullscreen_window:
            self.fullscreen_window = ImageViewer(self.master, self.image_path, None, True)

    def control_f(self, event):
        self.create_fullscreen_window()

    def reset_window_width_height(self):
        self.window_width = self.screen_width

        if not self.create_fullscreen:
            shrink_by = IMAGE_WINDOW_OFFSET
        else:
            shrink_by = MENU_BAR_THICKNESS
        self.window_height = self.screen_height - shrink_by  # arbitrary subtracted value

    def load_image(self):
        self.reset_window_width_height()
        self.image_original = Image.open(self.image_path)
        self.image_original = exif_orientation.correct_image_orientation(self.image_original)
        self.top.title(self.image_path)
        self.create_thumbnail()
        
    def create_thumbnail(self):
        self.image_thumbnail = self.image_original.copy()
        self.image_thumbnail.thumbnail((self.window_width, self.window_height), Image.ANTIALIAS)
        self.image_tk = ImageTk.PhotoImage(self.image_thumbnail)

    def draw_image(self):
        self.label.configure(image=self.image_tk)

    def resized(self, event):
        self.window_width = event.width
        self.window_height = event.height
        logging.debug('*****************************')
        logging.debug('window dimensions: %d, %d' % (event.width, event.height))
        logging.debug('image dimentions: %d, %d' % (self.image_tk.width(), self.image_tk.height()))
        self.create_thumbnail()
        self.draw_image()

    
if __name__ == '__main__':    
    master = Tk()
    im = ImageViewer(master, '/Users/bcox/Pictures/Cambodia/IMG_0474.JPG', None, False)
    master.mainloop()
