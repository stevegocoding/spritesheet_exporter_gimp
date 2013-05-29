__author__ = 'Guangfu Shi'


import gimpfu
import gtk
import io

PWF_STATE = 10001
PWF_STATE_NAME = 100015
PWF_TILE_X = 10002
PWF_TILE_Y = 10003
PWF_NUM_FRAMES = 10004


class EntryValueError(Exception):
    pass


class StringEntry(gtk.Entry):
    def __init__(self, default=""):
        gtk.Entry.__init__(self)
        self.set_text(str(default))

    def get_value(self):
        return self.get_text()


class IntEntry(StringEntry):
    def get_value(self):
        try:
            return int(self.get_text())
        except ValueError, e:
            raise EntryValueError, e.args


class ComboEntry(gtk.ComboBox):
    def __init__(self, default=0, items=()):
        store = gtk.ListStore(str)
        for item in items:
            store.append([item])

        gtk.ComboBox.__init__(self, model=store)

        cell = gtk.CellRendererText()
        self.pack_start(cell)
        self.set_attributes(cell, text=0)

        self.set_active(default)

    def get_value(self):
        return self.get_active_text()


class AnimationState(object):
    four_directions = ("n", "w", "s", "e")

    def __init__(self, name, img_tile_x, img_tile_y, num_frames, directions):
        self._name = name
        self._img_tile_x = img_tile_x
        self._img_tile_y = img_tile_y
        self._num_frames = num_frames
        self._directions = directions

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, val):
        self._name = val

    @property
    def tile_xy(self):
        return self._img_tile_x, self._img_tile_y

    @tile_xy.setter
    def tile_xy(self, val):
        self._img_tile_x = val.x
        self._img_tile_y = val.y

    @property
    def num_frames(self):
        return self._num_frames

    @num_frames.setter
    def num_frames(self, val):
        self._num_frames = val

    @property
    def num_directions(self):
        return self._directions

    @num_directions.setter
    def num_directions(self, val):
        self._directions = val


params = [
    (PWF_STATE, "state_cb", "State CB", "New"),
    (PWF_STATE_NAME, "state_name", "State Name", "new state"),
    (PWF_TILE_X, "tile_x", "Tile X", 0),
    (PWF_TILE_Y, "tile_y", "Tile Y", 0),
    (PWF_NUM_FRAMES, "num_frames", "Frames", 0)
]

states_data = {}


def append_state(name="default", tile_x=0, tile_y=0, num_frames=0, directions=4):
    if name in states_data:
        state = states_data[name]
        state.name = name
        state.tile_xy = (tile_x, tile_y)
        state.num_frame = num_frames
        state.num_directions = directions
    else:
        state = AnimationState(name, tile_x, tile_y, num_frames, directions)
        states_data[name] = state


def remove_state(name):
    if name in states_data:
        del states_data[name]


class PluginGUI(object):
    def __init__(self, params, image, sprite_size):
        # Dialog and Container
        self._dialog = gtk.Dialog(title="Spritesheet Exporter",
                                  parent=None,
                                  flags=0,
                                  buttons=(gtk.STOCK_OK, gtk.RESPONSE_CLOSE,
                                           "Export", gtk.RESPONSE_APPLY))

        self._image = image
        self._sprite_width = sprite_size[0]
        self._sprite_height = sprite_size[1]

        self._vbox = gtk.VBox(False, 12)
        self._vbox.set_border_width(12)
        self._dialog.vbox.pack_start(self._vbox)
        self._vbox.show()
        self._table = gtk.Table(5, 4, False)
        self._table.set_row_spacings(6)
        self._table.set_col_spacings(6)
        self._vbox.pack_start(self._table, expand=False)
        self._table.show()

        # Widgets
        self._state_cb_entry = ComboEntry()
        self._state_name_entry = StringEntry()
        self._state_tile_x_entry = StringEntry()
        self._state_tile_y_entry = StringEntry()
        self._state_num_frames_entry = StringEntry()

        self._add_state_btn = gtk.Button("Add/Update")
        self._add_state_btn.connect("clicked", self.add_update_state, None)
        self._add_state_btn.show()
        self._remove_state_btn = gtk.Button("Remove")
        self._remove_state_btn.connect("clicked", self.remove_state, None)
        self._remove_state_btn.show()

        self._state_cb_entry.connect("changed", self.on_state_cb_changed)
        self._dialog.connect("response", self.response)

        for i in range(len(params)):
            pf_type = params[i][0]
            name = params[i][1]
            desc = params[i][2]
            def_val = params[i][3]
            label = gtk.Label(desc)
            label.set_use_underline(True)
            label.set_alignment(0.0, 0.5)
            self._table.attach(label, 1, 2, i, i+1, xoptions=gtk.FILL)
            label.show()

            wid = None
            if pf_type == PWF_STATE:
                wid = self._state_cb_entry
                self._table.attach(self._add_state_btn, 3, 4, i, i+1, yoptions=0)
                self._table.attach(self._remove_state_btn, 4, 5, i, i+1, yoptions=0)
            elif pf_type == PWF_STATE_NAME:
                wid = self._state_name_entry
            elif pf_type == PWF_TILE_X:
                wid = self._state_tile_x_entry
            elif pf_type == PWF_TILE_Y:
                wid = self._state_tile_y_entry
            elif pf_type == PWF_NUM_FRAMES:
                wid = self._state_num_frames_entry

            label.set_mnemonic_widget(wid)
            self._table.attach(wid, 2, 3, i, i+1, yoptions=0)
            wid.show()
            wid.desc = desc

        self._dialog.show()
        self._dialog.run()
        #gtk.main()

    def response(self, dialog, response_id):
        if response_id == gtk.RESPONSE_CLOSE:
            gtk.main_quit()
        elif response_id == gtk.RESPONSE_APPLY:
            chooser = gtk.FileChooserDialog(title=None,
                                            action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                            buttons=(gtk.STOCK_CANCEL,
                                                     gtk.RESPONSE_CANCEL,
                                                     gtk.STOCK_SAVE,
                                                     gtk.RESPONSE_OK))
            response = chooser.run()
            if response == gtk.RESPONSE_OK:
                file_name = chooser.get_filename()
                self.do_export(file_name)

            chooser.destroy()

    def add_update_state(self, widget, data=None):
        name = self._state_name_entry.get_value()
        tile_x = self._state_tile_x_entry.get_value()
        tile_y = self._state_tile_y_entry.get_value()
        num_frames = self._state_num_frames_entry.get_value()
        append_state(name, tile_x, tile_y, num_frames, 4)
        self._state_cb_entry.append_text(name)

    def remove_state(self, widget, data=None):
        name = self._state_cb_entry.get_active_text()
        gimpfu.pdb.gimp_message(name)
        if name is not None:
            remove_state(name)
            idx = self._state_cb_entry.get_active()
            self._state_cb_entry.remove_text(idx)

    def on_state_cb_changed(self, cb):
        name = cb.get_active_text()
        if name in states_data:
            #gimpfu.pdb.gimp_message(name)
            tile_xy = states_data[name].tile_xy
            num_frames = states_data[name].num_frames
            self._state_name_entry.set_text(name)
            self._state_tile_x_entry.set_text(tile_xy[0])
            self._state_tile_y_entry.set_text(tile_xy[1])
            self._state_num_frames_entry.set_text(num_frames)

    def do_export(self, file_name):
        with io.open(file_name, 'w+') as file_handle:
            write_str = "test string".decode("utf-8")
            file_handle.write(write_str)
            for state in states_data.values():
                name = state.name
                for dir in AnimationState.four_directions:
                    state_dir = name + dir
                    for idx in range(state.num_frames):
                        state_dir.join(str(idx))
                        gimpfu.pdb.gimp_message(state_dir)
                        file_handle.write(state_dir)

            file_handle.close()


def plugin_main(image, drawable, sprite_width, sprite_height, layer):

    gui = PluginGUI(params, image, (sprite_width, sprite_height))

gimpfu.register(
    "python-fu-spritesheet-exporter",
    "Exports a spritesheet with animations",
    "Exports a xml file describing the animation",
    "Guangfu Shi",
    "Guangfu Shi",
    "2013",
    "<Image>/Image/Spritesheet Exporter...",
    "RGB*, GRAY*",
    [
        (gimpfu.PF_INT, "sprite_width", "Sprite Width", 64),
        (gimpfu.PF_INT, "sprite_height", "Sprite Height", 64),
        (gimpfu.PF_LAYER, "active_layer", "Layer", None)
    ],
    [],
    plugin_main
)

gimpfu.main()