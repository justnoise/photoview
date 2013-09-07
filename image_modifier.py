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
from PIL import Image
import tkFileDialog
import os
import image_scroll_frame
import exif_orientation
import logging
import argparse
import pdb

source_label = 'Source:        '
destination_label = 'Destination: '


class DirectoryChooser(Frame):
    def __init__(self, parent, directory_changed_callback, dir_name, dir_must_exist = False, **args):
        Frame.__init__(self, parent, **args)
        self.parent = parent
        self.directory_changed_callback = directory_changed_callback
        self.dir_must_exist = dir_must_exist

        self.dir_label = Label(self, text=dir_name)
        self.dir_label.pack(side = LEFT)
        self.dir_var = StringVar()
        self.dir_edit = Entry(self, textvariable=self.dir_var)
        self.dir_edit.pack(side = LEFT, fill=X, expand=True)
        self.dir_browse = Button(self, text='Browse...', command=self.browse_action)
        self.dir_browse.pack(side = RIGHT)

    def set_directory(self, directory):
        self.dir_var.set(directory)

    def browse_action(self):
        dir_opt = options = {}
        options['mustexist'] = self.dir_must_exist
        options['parent'] = self.parent
        options['title'] = 'Select an image directory'
        ret_val = tkFileDialog.askdirectory(**dir_opt)
        logging.info(str(ret_val))
        if ret_val:
            self.dir_var.set(ret_val)
            the_dir = self.dir_var.get()
            if the_dir and self.directory_changed_callback:
                self.directory_changed_callback(the_dir)
                #self.image_frame.load_all_images_from_directory(the_dir)


class MoveModifierFrame(Frame):
    def __init__(self, 
                 parent, 
                 source_changed_callback,
                 destination_changed_callback,
                 button_action,
                 **args):
        Frame.__init__(self, parent, **args)
        self.parent = parent
        
        self.source_chooser = DirectoryChooser(self, source_changed_callback, source_label, dir_must_exist=True)
        self.source_chooser.pack(fill = X, expand = 1)
        self.destination_chooser = DirectoryChooser(self, destination_changed_callback, destination_label, dir_must_exist=False)
        self.destination_chooser.pack(fill = X, expand= 1)

        self.button_frame = Frame(self)
        self.modify_button = Button(self.button_frame, text='Move', command=button_action)
        self.button_frame.pack(fill=X, expand=0)
        self.modify_button.pack()


class SizeModifierFrame(Frame):
    def __init__(self, 
                 parent, 
                 source_changed_callback,
                 destination_changed_callback,
                 button_action,
                 **args):
        Frame.__init__(self, parent, **args)
        self.parent = parent
        
        self.source_chooser = DirectoryChooser(self, source_changed_callback, source_label, dir_must_exist=True)
        self.source_chooser.pack(fill = X, expand = 1)
        self.destination_chooser = DirectoryChooser(self, destination_changed_callback, destination_label, dir_must_exist=False)
        self.destination_chooser.pack(fill = X, expand = 1)

        self.size_frame = Frame(self)
        self.size_var = IntVar()
        self.size_var.set(800)
        self.size_entry = Entry(self.size_frame, textvariable=self.size_var)
        self.size_frame.pack(fill = X, expand = 1)
        
        Label(self.size_frame, text='Longest side length: ').pack(side=LEFT)
        self.size_entry.pack(side=LEFT)
        Label(self.size_frame, text='pixles').pack(side=LEFT)

        self.button_frame = Frame(self)
        self.modify_button = Button(self.button_frame, text='Resize', command=button_action)
        self.button_frame.pack(fill=X, expand=0)
        self.modify_button.pack()

    def get_size(self):
        return self.size_var.get()


class CommentModifierFrame(Frame):
    def __init__(self, 
                 parent, 
                 source_changed_callback,
                 button_action,
                 **args):
        Frame.__init__(self, parent, **args)
        self.parent = parent

        self.source_chooser = DirectoryChooser(self, source_changed_callback, source_label, dir_must_exist=True)
        self.source_chooser.pack(fill = X, expand = 1)
        comment_frame = Frame(self)
        comment_frame.pack(fill = X, expand = 1)
        comment_label = Label(comment_frame, text='Comment:   ')
        comment_label.pack(side=LEFT)

        text_frame = Frame(comment_frame)
        text_frame.pack(side=LEFT, fill = X, expand = 1)
        self.text_widget = Text(text_frame, height=3, relief=SUNKEN, borderwidth=1, wrap=WORD)
        scroll = Scrollbar(text_frame, command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scroll.set)
        self.text_widget.pack(side=LEFT, fill=BOTH, expand=1)
        scroll.pack(side=RIGHT, fill=Y)

        self.button_frame = Frame(self)
        self.modify_button = Button(self.button_frame, text='Add Comment', command=button_action)
        self.button_frame.pack(fill=X, expand=0)
        self.modify_button.pack()

    def set_text(self, text):
        self.text_widget.delete(1.0, END)
        self.text_widget.insert(END, text)

    def get_text(self):
        text = self.text_widget.get(1.0, END)
        if text[-1] == '\n':
            return text[:-1]
        else:
            return text


class ImageModifier(object):
    def __init__(self, parent):
        top_frame = Frame(parent)

        self.source_directory = None
        self.destination_directory = None
        self.source_image_frame = image_scroll_frame.ImageScrollFrame(top_frame)
        self.destination_image_frame = image_scroll_frame.ImageScrollFrame(top_frame)

        top_frame.pack(fill=BOTH, expand=1)
        self.source_image_frame.pack(side=LEFT, fill=BOTH, expand=1)
        self.destination_image_frame.pack(side=RIGHT, fill=BOTH, expand=1)

        mid_frame = Frame(parent)
  
        radio_frame = Frame(mid_frame, relief=GROOVE, borderwidth=1)
        radio_frame.pack(side=LEFT, ipadx=2, padx=10, fill=BOTH)
        self.modifier_var = IntVar()
        radio_data = [('Move', 1, self.change_to_move_modifier), 
                      ('Size', 2, self.change_to_size_modifier), 
                      ('Comment', 3, self.change_to_comment_modifier)]
        for text, value, callback in radio_data:
            r = Radiobutton(radio_frame, text=text, 
                            value=value, variable=self.modifier_var, 
                            indicatoron=1, command=callback)
            r.pack(anchor=W, ipadx=1)
        self.modifier_var.set(1)
        self.move_modifier_frame = MoveModifierFrame(mid_frame,
                                                     self.change_source_directory,
                                                     self.change_destination_directory,
                                                     self.move_files,
                                                     relief=GROOVE, borderwidth=1)
        self.size_modifier_frame = SizeModifierFrame(mid_frame,
                                                     self.change_source_directory,
                                                     self.change_destination_directory,
                                                     self.resize_files,
                                                     relief=GROOVE, borderwidth=1)
        self.comment_modifier_frame = CommentModifierFrame(mid_frame,
                                                           self.change_source_directory,
                                                           self.write_comment,
                                                           relief=GROOVE, borderwidth=1)
        
        self.current_modifier_frame = None
        mid_frame.pack(fill=X, expand=0)
        self.change_modifier(self.move_modifier_frame)

    def change_source_directory(self, directory):
        self.source_directory = directory
        self.source_image_frame.load_all_images_from_directory(self.source_directory)
        self.move_modifier_frame.source_chooser.set_directory(directory)
        self.size_modifier_frame.source_chooser.set_directory(directory)
        self.comment_modifier_frame.source_chooser.set_directory(directory)

    def change_destination_directory(self, directory):
        self.destination_directory = directory
        self.destination_image_frame.load_all_images_from_directory(self.destination_directory)
        self.move_modifier_frame.destination_chooser.set_directory(directory)
        self.size_modifier_frame.destination_chooser.set_directory(directory)

    def unpack_comment_modifier(self):
        self.source_image_frame.single_selection = False
        self.destination_image_frame.pack(side=RIGHT, fill=BOTH, expand=1)
        self.source_image_frame.single_click_callback = None
        self.comment_modifier_frame.pack_forget()

    def change_to_move_modifier(self):
        if self.current_modifier_frame == self.comment_modifier_frame:
            self.unpack_comment_modifier()
        self.change_modifier(self.move_modifier_frame)
        self.source_image_frame.update_all_image_callbacks()

    def change_to_size_modifier(self):
        if self.current_modifier_frame == self.comment_modifier_frame:
            self.unpack_comment_modifier()
        self.change_modifier(self.size_modifier_frame)
        self.source_image_frame.update_all_image_callbacks()
        
    def change_to_comment_modifier(self):
        self.destination_image_frame.pack_forget()
        self.source_image_frame.unselect_all_images()
        self.source_image_frame.single_selection = True
        self.source_image_frame.single_click_callback = self.display_comment_for_image
        self.source_image_frame.update_all_image_callbacks()
        self.change_modifier(self.comment_modifier_frame)

    def change_modifier(self, new_modifier):
        if self.current_modifier_frame != new_modifier:
            if self.current_modifier_frame:
                self.current_modifier_frame.pack_forget()
            self.current_modifier_frame = new_modifier
            self.current_modifier_frame.pack(fill=X, expand=1, ipadx=2, ipady=2)

    def move_files(self):
        if (not os.path.isdir(self.source_directory) or 
            not os.path.isdir(self.destination_directory)):
            #todo, make this a message box
            logging.error('source or destination does not exist or is not a folder')
            return
        if self.source_directory == self.destination_directory:
            logging.error('source directory is the same as destionation directory')
            return

        selected_image_paths = self.source_image_frame.get_selected_image_paths()
        logging.info(selected_image_paths)
        for source_path in selected_image_paths:
            image_name = os.path.basename(source_path)
            destination_path = os.path.join(self.destination_directory, image_name)
            logging.info(''.join([source_path, destination_path]))
            if os.path.exists(destination_path):
                logging.warning('SKIPPING: %s: FILE EXISTS' % destination_path)
                continue
            else:
                os.rename(source_path, destination_path)
        if selected_image_paths:
            self.source_image_frame.load_all_images_from_directory(self.source_directory)
            self.destination_image_frame.load_all_images_from_directory(self.destination_directory)

    def resize_files(self):
        def get_value():
            size = self.size_var.get()
            # if size is not a valid integer, None is returned
            # could use a better warning message...
            return size
        def verify_value(v):
            return v and 0 < v < 5000
        
        size = self.size_modifier_frame.get_size()
        # todo, edit box should verify this value, use lose focus callback
        if not verify_value(size):
            logging.error('Invalid value for size: %s' % str(size))
        else:
            selected_image_paths = self.source_image_frame.get_selected_image_paths()
            logging.debug(selected_image_paths)
            for source_path in selected_image_paths:
                image_name = os.path.basename(source_path)
                image_name_parts = os.path.splitext(image_name)
                image_name = image_name_parts[0] + '_resized_' + str(size) + image_name_parts[1]
                destination_path = os.path.join(self.destination_directory, image_name)
                logging.debug(''.join([source_path, destination_path]))
                if os.path.exists(destination_path):
                    logging.warning('SKIPPING: %s: FILE EXISTS' % destination_path)
                    continue
                else:
                    try:
                        image = Image.open(source_path)
                        image = exif_orientation.correct_image_orientation(image)
                        image.thumbnail((size, size), Image.ANTIALIAS)
                        image.save(destination_path)
                    except Exception as e:
                        logging.error('Error resizing image: %s' % source_path)
                        logging.error(str(e))
            if selected_image_paths:
                self.source_image_frame.unselect_all_images()
                self.destination_image_frame.load_all_images_from_directory(self.destination_directory)


    def get_comment_file_path(self, image_path):
        name, ext = os.path.splitext(image_path)
        name += '_comment'
        ext = '.txt'
        return name + ext

    def display_comment_for_image(self, image_path):
        comment_file_path = self.get_comment_file_path(image_path)
        data = ''
        if os.path.exists(comment_file_path):
            data = open(comment_file_path, 'r').read()
        self.comment_modifier_frame.set_text(data)

    def get_single_selected_image(self):
        selected_image_path = self.source_image_frame.get_selected_image_paths()
        if selected_image_path:
            return selected_image_path[0]
        else:
            return None

    def write_comment(self):
        selected_image_path = self.get_single_selected_image()
        if selected_image_path:
            comment_data = self.comment_modifier_frame.get_text()
            comment_file_path = self.get_comment_file_path(selected_image_path)
            open(comment_file_path, 'w').write(comment_data)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Organize Photos.')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='turn on verbose output')
    args = parser.parse_args()
    return args

def init_logging(args):
    '''we log everyting to the console, this is mostly
    for debugging window positions and other issues'''

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)


if __name__ == '__main__':
    args = parse_arguments()
    init_logging(args)
    master = Tk()
    master.geometry('1200x800')     # looks good for me!  Don't know about you suckers...
    mmf = ImageModifier(master)
    master.mainloop()
