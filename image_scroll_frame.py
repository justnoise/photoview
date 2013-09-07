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
import glob
import math
import threading
import Queue
import os.path
import logging

import pdb

from image_viewer import ImageViewer
import selectable_image
import exif_orientation

image_box = selectable_image.thumbnail_size[0] + selectable_image.thumbnail_padding + 15

THUMBNAIL_METHOD = Image.BILINEAR
#THUMBNAIL_METHOD = Image.BICUBIC
#THUMBNAIL_METHOD = Image.ANTIALIAS

SELECTED = True
UNSELECTED = False

class ImageScrollFrame(Frame):    
    def __init__(self, parent, **options):

        # if 'single_selection' in options:
        #     self.single_selection = options['single_selection']
        #     del(options['single_selection'])

        Frame.__init__(self, parent, **options)
        self.parent = parent

        self.images = []
        self.image_paths = []
        self.num_images = 0
        self.last_selected = (None, None)

        self.single_selection = False

        self.canvas_height = 0
        self.canvas_width = 0
        self.num_cols = 0
        self.num_rows = 0

        self.canvas = Canvas(parent, relief=FLAT, borderwidth=0)
        self.vscroll = Scrollbar(parent, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vscroll.set)

        self.pack(expand=YES, fill=BOTH, padx=1, pady=1)
        self.rowconfigure(0, weight=1, minsize=0)
        self.columnconfigure(0, weight=1, minsize=200)
        self.canvas.grid(padx=1, in_=self, pady=1, row=0,
                         column=0, rowspan=1, columnspan=1, sticky='news')
        self.vscroll.grid(padx=1, in_=self, pady=1, row=0,
                          column=1, rowspan=1, columnspan=1, sticky='news')
        self.canvas.bind('<MouseWheel>', self.scrollwheel)
        self.canvas.bind("<Configure>", self.window_resize)
        
        self.single_click_callback = None

    def window_resize(self, event):
        self.canvas.after_idle(self.layout_all_images)

    def scrollwheel(self, event):
        if event.state == 0:
            # need to see how this works on other systems, its backwards on OSX
            self.canvas.yview('scroll', -event.delta, 'units') 

    def get_num_rows_and_cols(self):
        width = int(self.canvas.winfo_width())
        num_cols = max(1, int(width) / (image_box))
        num_rows = int(math.ceil( self.num_images / float(num_cols) ))
        return num_rows, num_cols

    def layout_single_image(self, image_index, image):
        num_rows, num_cols = self.get_num_rows_and_cols()
        half_image_box = image_box / 2
        row = image_index / num_cols
        col = image_index - (row * num_cols)
        center_x = col * image_box + half_image_box
        center_y = row * image_box + half_image_box
        image.draw(center_x, center_y)

    def delete_image_layout(self):
        for i in self.images:
            i.erase()

    def layout_all_images(self):
        self.delete_image_layout()
        
        for i, image in enumerate(self.images):
            self.layout_single_image(i, image)
        num_rows, num_cols = self.get_num_rows_and_cols()
        self.canvas.config(scrollregion=(0,0,num_cols*image_box, num_rows * image_box))

    def single_clicked_image(self, image):
        logging.debug('from parent: single clicked on ' + image.image_path)
        if image.selected:
            self.last_selected = (image, SELECTED)
        else:
            self.last_selected = (image, UNSELECTED)

        if self.single_selection:
            # remove selections that aren't image not all that
            # efficient but I'd rather not cache selections unless it
            # becomes an issue
            for i, img in enumerate(self.images):
                if img != image and img.selected:
                    img.toggle_selection()
            
        if self.single_click_callback and image.selected:
            self.single_click_callback(image.image_path)
            
    def shift_clicked_image(self, image):
        '''Implementation of shift selection kinda stinks...

        there is two ways of doing this. In the first method, keep a
        list of selected items when you click on an item, it gets
        added to the head/tail of the list, when you unselect
        something, remove it from the list.  When shift clicking,
        choose the item from the head/tail of the list and link that
        to the clicked on item.  Also keep track of successive shift
        selections...

        Otherwise (Mr. Bobo method!):
        Just keep a last_selected member.  When you select an item,
        that becomes the last_selected member.  If you unselect the
        last_selected member, you cannot do a range select.  This also
        allows you to shift-click to select a large range of items
        then shift-click to unselect a subrange of those items.

        '''
        if self.last_selected[0]:
            selected_or_unselected = self.last_selected[1]
            last_selected_index = self.images.index(self.last_selected[0])
            this_selected_index = self.images.index(image)

            begin = min(this_selected_index, last_selected_index)
            end = max(this_selected_index, last_selected_index)
            for image_index in range(begin, end+1):
                cur_image = self.images[image_index]
                cur_image.selected = selected_or_unselected
                cur_image.draw_selection()

    def double_clicked_image(self, image):
        logging.info('double clicked on ' + image.image_path)
        ImageViewer(self.parent, image.image_path, self.image_paths)

    def get_selected_image_paths(self):
        return [image.image_path for image in self.images if image.selected]

    def unselect_all_images(self):
        for image in self.images:
            image.selected = False
        self.layout_all_images()

    def selectable_image_factory(self, image_path, tk_image):
        image = selectable_image.SelectableImage(self.canvas, image_path, tk_image)
        self.update_image_callbacks(image)
        return image

    def update_image_callbacks(self, image):
        image.single_click_callback = self.single_clicked_image
        image.double_click_callback = self.double_clicked_image
        if not self.single_selection:
            image.shift_click_callback = self.shift_clicked_image
        else:
            image.shift_click_callback = self.single_clicked_image

    def update_all_image_callbacks(self):
        for image in self.images:
            self.update_image_callbacks(image)

    def add_images_mt(self, image_paths):
        self.delete_image_layout()
        self.image_paths = image_paths
        self.images = []
        self.num_images = len(self.image_paths)
        num_rows, num_cols = self.get_num_rows_and_cols()
        self.canvas.config(scrollregion=(0,0,num_cols*image_box, num_rows * image_box))

        #create thread to load images
        self.mt_queue = Queue.Queue()
        self.the_thread = threading.Thread(target=self.create_image_buttons_mt, 
                                           args=(image_paths, self.mt_queue))
        self.parent.after(250, self.check_for_new_images())
        self.the_thread.start()

    def check_for_new_images(self):
        # get things out of the synchronized queue, create buttons,
        # add them to the window
        done = False
        while not self.mt_queue.empty():
            image_path, image_tn = self.mt_queue.get()
            # this next image conversion has to run in the main thread
            tk_image = ImageTk.PhotoImage(image_tn)
            image = self.selectable_image_factory(image_path, tk_image)

            self.images.append(image)
            image_index = len(self.images) - 1
            self.layout_single_image(image_index, image)
            if image_path == self.image_paths[-1]:
                done = True
        # set the timer to look for more images
        if not done:
            self.parent.after(200, self.check_for_new_images)
        else:
            self.layout_all_images()

    def create_image_buttons_mt(self, image_paths, mt_queue):
        for image_path in image_paths:
            # load the images
            image_tn = Image.open(image_path)
            image_tn = exif_orientation.correct_image_orientation(image_tn)
            image_tn.thumbnail(selectable_image.thumbnail_size, THUMBNAIL_METHOD)
            # create tuple and place into queue
            data = (image_path, image_tn)
            mt_queue.put(data)

    def load_all_images_from_directory(self, directory):
        files = glob.glob(os.path.join(directory, '*.jpg'))
        upper_files = glob.glob(os.path.join(directory, '*.JPG'))
        files += upper_files
        logging.info(str(files))
        self.add_images_mt(files)
        

def do_test():
    def get_files():
        import glob
        folder = '/Users/bcox/Pictures/ColoradoWyoming/'
        files = glob.glob(folder + '*.jpg')
        upper_files = glob.glob(folder + '*.JPG')
        files += upper_files
        logging.info(str(files))
        return files

    master = Tk()
    master.geometry('900x800')
    isc = ImageScrollFrame(master, height = 500, width = 500)
    isc.pack(fill=BOTH, expand = 1)
    #isc.add_images_mt(files)
    isc.load_all_images_from_directory('/Users/bcox/Pictures/ColoradoWyoming/')
    master.mainloop()
    
if __name__ == '__main__':
    do_test()
