import os
import cadquery as cq
from modulefinder import ModuleFinder
import numpy as np

from spyder.plugins.editor.widgets.codeeditor import CodeEditor
from PyQt5.QtCore import pyqtSignal, QFileSystemWatcher, QTimer
from PyQt5.QtWidgets import QAction, QFileDialog
from PyQt5.QtGui import QFontDatabase, QColor
from path import Path
from ..cq_utils import make_AIS, export, to_occ_color, is_obj_empty, get_occ_color
from ..occ.step_reader import read_step
from ..cq_utils import find_cq_objects, reload_cq
from types import SimpleNamespace

import sys

from pyqtgraph.parametertree import Parameter

from ..mixins import ComponentMixin
from ..utils import get_save_filename, get_open_filename, confirm, get_open_directory

from ..icons import icon

def get_track_color(charge):
    charge=float(charge)
    if charge<0:
        return (1,0,0)
    if charge==0:
        return (0,1,0)
    if charge>0:
        return (0,0,1)
def get_range(x, nstd=1, margin=None):
    m=np.mean(x)
    if margin is None:
        margin=nstd*np.std(x)
    return [m-margin, m+margin]

class Editor(CodeEditor,ComponentMixin):

    name = 'Code Editor'

    # This signal is emitted whenever the currently-open file changes and
    # autoreload is enabled.
    triggerRerender = pyqtSignal(bool)
    executeScript=pyqtSignal(str)
    sigFilenameChanged = pyqtSignal(str)
    addObjectsToScene= pyqtSignal(dict)

    preferences = Parameter.create(name='Preferences',children=[
        {'name': 'Font size', 'type': 'int', 'value': 12},
        {'name': 'Autoreload', 'type': 'bool', 'value': False},
        {'name': 'Autoreload delay', 'type': 'int', 'value': 50},
        {'name': 'Autoreload: watch imported modules', 'type': 'bool', 'value': False},
        {'name': 'Line wrap', 'type': 'bool', 'value': False},
        {'name': 'Max Tracks', 'type': 'int', 'value': 100},
        {'name': 'Color scheme', 'type': 'list',
         'values': ['Spyder','Monokai','Zenburn'], 'value': 'Spyder'}])

    EXTENSIONS = 'py'
    CAD_FILE_EXTENSIONS=['stp','step','STEP','STP',"*"]

    def __init__(self,parent=None):

        self._watched_file = None

        super(Editor,self).__init__(parent)
        ComponentMixin.__init__(self)

        self.setup_editor(linenumbers=True,
                          markers=True,
                          edge_line=False,
                          tab_mode=False,
                          show_blanks=True,
                          font=QFontDatabase.systemFont(QFontDatabase.FixedFont),
                          language='Python',
                          filename='')

        self.figviewer=None
        self.fig=None
        self._actions =  \
                {'File' : [QAction(icon('new'),
                                  'New',
                                  self,
                                  shortcut='ctrl+N',
                                  triggered=self.new),
                          QAction(icon('open'),
                                  'Open Script',
                                  self,
                                  shortcut='ctrl+O',
                                  triggered=self.open),

                          QAction(icon('import'),
                                  'Import',
                                  self,
                                  shortcut='ctrl+I',
                                  triggered=self.import_cad),

                          QAction(icon('import'),
                                  'Load G4 tracks',
                                  self,
                                  shortcut='ctrl+T',
                                  triggered=self.import_tracks),



                          QAction(icon('export'),
                                  'Export',
                                  self,
                                  shortcut='ctrl+I',
                                  triggered=self.export_gdml),

                        
                        
                          QAction(icon('save'),
                                  'Save',
                                  self,
                                  shortcut='ctrl+S',
                                  triggered=self.save),
                          QAction(icon('save_as'),
                                  'Save as',
                                  self,
                                  shortcut='ctrl+shift+S',
                                  triggered=self.save_as),
                          QAction(icon('autoreload'),
                                  'Automatic reload and preview',
                                  self,triggered=self.autoreload,
                                  checkable=True,
                                  checked=False,
                                  objectName='autoreload'),
                          ]}

        for a in self._actions.values():
            self.addActions(a)


        self._fixContextMenu()

        # autoreload support
        self._file_watcher = QFileSystemWatcher(self)
        # we wait for 50ms after a file change for the file to be written completely
        self._file_watch_timer = QTimer(self)
        self._file_watch_timer.setInterval(self.preferences['Autoreload delay'])
        self._file_watch_timer.setSingleShot(True)
        self._file_watcher.fileChanged.connect(
                lambda val: self._file_watch_timer.start())
        self._file_watch_timer.timeout.connect(self._file_changed)

        self.updatePreferences()

    def _fixContextMenu(self):

        menu = self.menu

        menu.removeAction(self.run_cell_action)
        menu.removeAction(self.run_cell_and_advance_action)
        menu.removeAction(self.run_selection_action)
        menu.removeAction(self.re_run_last_cell_action)

    def updatePreferences(self,*args):

        self.set_color_scheme(self.preferences['Color scheme'])

        font = self.font()
        font.setPointSize(self.preferences['Font size'])
        self.set_font(font)

        self.findChild(QAction, 'autoreload') \
            .setChecked(self.preferences['Autoreload'])

        self._file_watch_timer.setInterval(self.preferences['Autoreload delay'])

        self.toggle_wrap_mode(self.preferences['Line wrap'])

        self._clear_watched_paths()
        self._watch_paths()

    def confirm_discard(self):

        if self.modified:
            rv =  confirm(self,'Please confirm','Current document is not saved - do you want to continue?')
        else:
            rv = True

        return rv

    def new(self):

        if not self.confirm_discard(): return

        self.set_text('')
        self.filename = ''
        self.reset_modified()

    def open(self):
        
        if not self.confirm_discard(): return
        curr_dir = Path(self.filename).abspath().dirname()
        fname = get_open_filename(self.EXTENSIONS, curr_dir)
        if fname != '':
            self.load_from_file(fname)

    def load_from_file(self,fname):

        self.set_text_from_file(fname)
        self.filename = fname
        self.reset_modified()

    def save(self):

        if self._filename != '':

            if self.preferences['Autoreload']:
                self._file_watcher.blockSignals(True)
                self._file_watch_timer.stop()

            with open(self._filename, 'w') as f:
                f.write(self.toPlainText())

            if self.preferences['Autoreload']:
                self._file_watcher.blockSignals(False)
                self.triggerRerender.emit(True)

            self.reset_modified()

        else:
            self.save_as()
    #added by Hualin 2021-12-27
    def import_cad(self):
        if not self.confirm_discard(): return
        curr_dir = Path(self.filename).abspath().dirname()
        fname = get_open_filename(self.CAD_FILE_EXTENSIONS, curr_dir)
        if fname != '':
            self.import_cad_to_scene(fname)
    def import_tracks(self):
        if not self.confirm_discard(): return
        curr_dir = Path(self.filename).abspath().dirname()
        #path = get_open_directory()
        fname = get_open_filename('csv', curr_dir)
        #if path is not None and os.path.isfile(path):
        #    fname=os.path.join(path, 'tracks.csv')
        #print(fname)
        self.import_g4_tracks(fname)



    def export_gdml(self, objects=None):
        pass

    def to_shape(self,step_objects):
        results={}
        unamed_i=0
        
        for o in step_objects:
            c=o['RGB']
            color=QColor.fromRgbF(c[0],c[1],c[2],0.1)
            #print(c)
            label=o['Name']
            if not label:
                label=f'Unamed_{unamed_i}'
            results[label]=SimpleNamespace(shape=o['CQ_OCP_TopDS'],options={'alpha':0.1, 'color':color})
        return results



    def import_cad_to_scene(self, fname):
        #passss
        #code=f'''result=cq.importers.importStep("{fname}")\nshow_object(result)'''
        #self.executeScript.emit(code)
        result=read_step(fname) 
        objects_f=self.to_shape(result)
        self.addObjectsToScene.emit(objects_f)

    def set_figview_handle(self,fv):
        self.figviewer=fv
        fv.clear()
        self.fig=fv.figure

    def import_g4_tracks(self,fname):
        """
        render track.csv file
        track.csv format:
        ====
        Event 0
        Track parent_id charge
        point_0 (x,y, z, edep)
        point_1
        ...

        """
        results={}
        tracks=[]
        ev=[]
        color=(1,0,0)


        track_profile=[]
        
        with open(fname) as fd:
            for line in fd:
                if 'Event' in line:
                    continue
                if 'Track' in line:
                    if ev:
                        tracks.append(
                                {'points': ev,
                                    'color':color,
                                    }
                                )
                    color=get_track_color(line.split()[2]) #color in the row track
                    ev=[]
                    continue
                cols=[float(x) for x in line.split()]
                if len(cols) !=4:
                    print('Length invalid', cols)

                ev.append(cols)
                track_profile.append(cols)

            if ev:
                tracks.append(
                        {'points': ev,
                                'color':color,
                                }
                        )
        
        track_profile=np.array(track_profile)
        objects_f={}

        for i, track in enumerate(tracks):
            if i> self.preferences['Max Tracks']:
                break
            try:
                c=track['color']
                color=QColor.fromRgbF(c[0],c[1],c[2],0)
                label=f'track_{i}'
                pnts=np.array(track['points'])
                #print("pont",pnts.shape)
                pnts=pnts[:,:-1].tolist()
                objects_f[label]=SimpleNamespace(shape=cq.Workplane("XY").polyline(pnts),
                        options={'alpha':0, 'color':color})
            except Exception as e:
                print(e) 

        self.addObjectsToScene.emit(objects_f)
        ax1 = self.fig.add_subplot(1,1, 1)
        x=track_profile[:,0]
        y=track_profile[:,1]
        z=track_profile[:,2]
        w=track_profile[:,3]


        x_range=[28,48]#get_range(x, margin=50)
        y_range=[-5,5]#get_range(y, margin=4)
        z_range=get_range(z, margin=4)
        hxy=ax1.hist2d(x,y,range=[x_range, y_range], bins=100, weights=w )
        ax1.set_xlabel('X (mm)')
        ax1.set_ylabel('Y (mm)')
        #clb=self.fig.colorbar(hxy, ax=ax1)
        #print('plot data')
        """
        ax1 = self.fig.add_subplot(2,2, 1)
        x=track_profile[:,0]
        y=track_profile[:,1]
        z=track_profile[:,2]
        w=track_profile[:,3]

        orgin=(-200, 0,1700)

        #r=np.sqrt((x-orgin[0])**2 +(y-orgin[1])**2 +(z-orgin[2])**2)

        x_range=get_range(x, margin=10)
        y_range=get_range(y, margin=3)
        z_range=get_range(z, margin=3)

        hxy=ax1.hist2d(x,y,range=[ x_range, y_range], bins=50, weights=w )
        ax1.set_xlabel('X (mm)')
        ax1.set_ylabel('Y (mm)')
        #clb=self.fig.colorbar(hxy, ax=ax1)

        ax2 = self.fig.add_subplot(2,2, 2)
        ax2.hist2d(y,z,range=[ y_range, z_range], bins=50, weights=w )
        ax2.set_xlabel('Y (mm)')
        ax2.set_ylabel('Z (mm)')
        #clb=self.fig.colorbar(h2d_xy, ax=ax)
        ax3 = self.fig.add_subplot(2,2, 3)
        ax3.hist2d(x,z,range=[ x_range, z_range], bins=(100,100), weights=w )
        ax3.set_xlabel('X (mm)')
        ax3.set_ylabel('Z (mm)')

        ax4 = self.fig.add_subplot(2,2, 4)

        nbins=100
        bins=np.linspace(-150,300,nbins)
        edep=np.zeros(nbins)
        for yi,wi in zip(x,w):
            edep[np.argmax(bins>yi)]+=wi
        ax4.plot(bins, edep)
        ax4.set_xlabel('X (mm)')
        ax4.set_ylabel('Energy (keV)')
        ax4.set_yscale('log')
        """
        self.figviewer.refresh()
        print('done')



    def save_as(self):

        fname = get_save_filename(self.EXTENSIONS)
        if fname != '':
            with open(fname,'w') as f:
                f.write(self.toPlainText())
                self.filename = fname

            self.reset_modified()

    def _update_filewatcher(self):
        if self._watched_file and (self._watched_file != self.filename or not self.preferences['Autoreload']):
            self._clear_watched_paths()
            self._watched_file = None
        if self.preferences['Autoreload'] and self.filename and self.filename != self._watched_file:
            self._watched_file = self._filename
            self._watch_paths()

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, fname):
        self._filename = fname
        self._update_filewatcher()
        self.sigFilenameChanged.emit(fname)

    def _clear_watched_paths(self):
        paths = self._file_watcher.files()
        if paths:
            self._file_watcher.removePaths(paths)

    def _watch_paths(self):
        if self._filename:
            self._file_watcher.addPath(self._filename)
            if self.preferences['Autoreload: watch imported modules']:
                module_paths =  self.get_imported_module_paths(self._filename)
                if module_paths:
                    self._file_watcher.addPaths(module_paths)

    # callback triggered by QFileSystemWatcher
    def _file_changed(self):
        # neovim writes a file by removing it first so must re-add each time
        self._watch_paths()
        self.set_text_from_file(self._filename)
        self.triggerRerender.emit(True)

    # Turn autoreload on/off.
    def autoreload(self, enabled):
        self.preferences['Autoreload'] = enabled
        self._update_filewatcher()

    def reset_modified(self):

        self.document().setModified(False)
        
    @property
    def modified(self):
        
        return self.document().isModified()

    def saveComponentState(self,store):

        if self.filename != '':
            store.setValue(self.name+'/state',self.filename)

    def restoreComponentState(self,store):

        filename = store.value(self.name+'/state',self.filename)

        if filename and filename != '':
            try:
                self.load_from_file(filename)
            except IOError:
                self._logger.warning(f'could not open {filename}')


    def get_imported_module_paths(self, module_path):

        finder = ModuleFinder([os.path.dirname(module_path)])
        imported_modules = []

        try:
            finder.run_script(module_path)
        except SyntaxError as err:
            self._logger.warning(f'Syntax error in {module_path}: {err}')
        else:
            for module_name, module in finder.modules.items():
                if module_name != '__main__':
                    path = getattr(module, '__file__', None)
                    if path is not None and os.path.isfile(path):
                        imported_modules.append(path)

        return imported_modules


if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    editor = Editor()
    editor.show()

    sys.exit(app.exec_())
