"""
A convenience widget for editing dicts through UI. 
"""
import PyQt4.QtGui as _Qtui
import PyQt4.QtCore as _Qt

def viewInDictEditor(name, 
                     dictionary, menu = None, 
                     windowtitle = "Dictionary Editor", 
                     destroysignal = None, 
                     editable = True, 
                     parent = None):
    """
    Factory function returning a QAction. Arguments:
       name            QAction has this name
       dictionary      QAction will open this dictionary in a DictEditor
       menu            QAction is inserted into this menu
       windowtitle     DictEditor will have this window title.
       destroysignal   This signal will close the dicteditor 
       editable        whether the user can edit the dictionary, 
                       or if it's just a viewer.
       parent          If menu is not supplied, 
                       this will be the action's parent
    For greater control, create one from the normal class and customize it."""
    
    @_Qt.pyqtSlot()
    def slot():
        editor = DictEditor(dictionary = dictionary, 
                            destroysignal = destroysignal, 
                            editable = editable)
        editor.setWindowTitle(windowtitle)
        editor.show()
        return
    if menu:
        a = menu.addAction(name, slot)
    else:
        a = _Qtui.QAction(name, parent)
        a.triggered.connect(slot)
    return a

class _Row(_Qtui.QWidget):
    """
    Row Widget from DictEditor.
    """
    contentsChanged = _Qt.pyqtSignal()
    changeSaved = _Qt.pyqtSignal((object, str, str, str),
                                 (object, int, str, str))
    deleted = _Qt.pyqtSignal(object)
    
    def __init__(self, key, value):
        super().__init__()
        self.editable = True
        self.initkey = key
        self.initvalue = value
        self.layout = _Qtui.QHBoxLayout()
        self.setLayout(self.layout)
        self.save = _Qtui.QPushButton("Save",self)
        self.remove = _Qtui.QPushButton("Delete",self)
        self.revert = _Qtui.QPushButton("Revert",self)
        self.key = _Qtui.QTextEdit(self)
        self.key.setText(str(self.initkey))
        self.key.setMaximumHeight(30)
        self.value = _Qtui.QTextEdit(self)
        self.value.setText(str(self.initvalue))
        self.value.setMaximumHeight(30)
        self.layout.addWidget(self.save,1)
        self.layout.addWidget(self.remove,1)
        self.layout.addWidget(self.revert,1)
        self.layout.addWidget(self.key,10)
        self.layout.addWidget(self.value,10)
        self.layout.setSizeConstraint(4)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.key.textChanged.connect(self.contentsChanged)
        self.value.textChanged.connect(self.contentsChanged)
        self.contentsChanged.connect(self.setChanged)
        self.save.setEnabled(False)
        self.revert.setEnabled(False)
        self.save.clicked.connect(self.saveChange)
        self.revert.clicked.connect(self.revertToInit)
        self.remove.clicked.connect(self.deleteMe)
        self.saved = True
        
    @_Qt.pyqtSlot()
    def deleteMe(self):
        self.deleted.emit(self)
        
    @_Qt.pyqtSlot(bool)
    def setEditable(self, bool):
        self.editable = bool
        
    @_Qt.pyqtSlot()
    def setChanged(self):
        if self.editable:
            self.save.setEnabled(True)
        self.revert.setEnabled(True)
        self.saved = False
        
    @_Qt.pyqtSlot()
    def saveChange(self):
        previouskey = self.initkey
        self.changeSaved.emit(self, 
                              str(previouskey), 
                              self.key.toPlainText(), 
                              self.value.toPlainText())
        
    def saveApproved(self):
        self.initkey = self.key.toPlainText()
        self.initvalue = self.value.toPlainText()
        self.save.setEnabled(False)
        self.revert.setEnabled(False)
        self.saved = True
        
    @_Qt.pyqtSlot()
    def revertToInit(self):
        self.contentsChanged.emit()
        self.key.setText(str(self.initkey))
        self.value.setText(str(self.initvalue))
        self.save.setEnabled(False)
        self.revert.setEnabled(False)
        self.saved = True
        
    def currentState(self):
        return self.initkey, self.initvalue

class DictEditor(_Qtui.QScrollArea):
    """
    Widget that allows editing of a dictionary in a user-friendly UI interface.
    
    Usage: DictEditor(dictionary, destroysignal = None, editable = True)
    
    Where:
        dictionary      The dictionary to be modified
        destroysignal   This signal will destroy the DictEditor
                            (can be used for cleanup actions). 
                        Must be a valid _Qt Signal or false boolean value.
        editable        Set to false to prohobit editing of the dictionary.
        
    Dictionaires are expected to use strings for keys. Integers used as keys
    won't break DictEditor, but when edited, they are converted to strings.
    """
    instancereflist = []
    
    def __init__(self, dictionary, destroysignal = None, editable = True):
        super().__init__()
        self.reflist = []
        if destroysignal is not None:
            destroysignal.connect(self.close)
        self.dictionary = dictionary
        self.setMinimumSize(400,130)
        self.layout = _Qtui.QVBoxLayout()
        self.contentarea = _Qtui.QWidget(self)
        self.setWidget(self.contentarea)
        self.contentarea.setLayout(self.layout)
        self.setWidgetResizable(True)
        self.editable = editable
        for k, v in dictionary.items():
            a = _Row(k, v)
            a.setEditable(self.editable)
            a.changeSaved.connect(self.writeToDict)
            a.deleted.connect(self.delete_Row)
            self.reflist.append(a)
            self.layout.addWidget(a)
        if self.editable:
            self.lastrow = _Row("","")
            self.layout.addWidget(self.lastrow)
            self.lastrow.changeSaved.connect(self.writeToDict)
            self.lastrow.changeSaved.connect(self.newlastrow)
            self.lastrow.deleted.connect(self.delete_Row)
            self.lastrow.remove.setEnabled(False)
        self.menu = self.buildmenu()
        self.instancereflist.append(self)
        return
        
    def closeEvent(self, event):
        self.instancereflist.pop(self.instancereflist.index(self))
        event.accept()
        
    def buildmenu(self):
        self.menubar = _Qtui.QMenuBar()
        self.menubar.setNativeMenuBar(False)
        self.layout.setMenuBar(self.menubar)
        self.actionsmenu = self.menubar.addMenu("&Actions")
        self.saveall_action = self.actionsmenu.addAction("Save All", 
                                                         self.saveall)
        self.undoall_action = self.actionsmenu.addAction("Undo All", 
                                                         self.undoall)
        self.close_action = self.actionsmenu.addAction("Close", self.close)
        
    @_Qt.pyqtSlot(object)
    def delete_Row(self, rowref):
        self.dictionary.pop(rowref.initkey)
        self.layout.removeWidget(rowref)
        rowref.hide()
        del rowref
        
    @_Qt.pyqtSlot()
    def saveall(self):
        [i.saveChange() for i in self.reflist if not i.saved]
                
    @_Qt.pyqtSlot()
    def undoall(self):
        [i.revertToInit() for i in self.reflist if not i.saved]
        
    @_Qt.pyqtSlot(object, str, str, str)
    @_Qt.pyqtSlot(object, int, str, str)
    def newlastrow(self, oldkey, key, value):
        self.lastrow.changeSaved.disconnect(self.newlastrow)
        self.lastrow.remove.setEnabled(True)
        self.reflist.append(self.lastrow)
        self.lastrow = _Row("","")
        self.layout.addWidget(self.lastrow)
        self.lastrow.changeSaved.connect(self.newlastrow)
        self.lastrow.changeSaved.connect(self.writeToDict)
        self.lastrow.deleted.connect(self.delete_Row)
        self.lastrow.remove.setEnabled(False)
        return
    
    @_Qt.pyqtSlot(object, str, str, str)
    @_Qt.pyqtSlot(object, int, str, str)
    def writeToDict(self, row, oldkey, key, value):
        if key != str(oldkey) and key in self.dictionary.keys():
            if not _Qtui.QMessageBox.Yes == \
                   _Qtui.QMessageBox.question(self,
                                              "Warning",
                                              "Changed key already exists in \
                                              dictionary.\nAre you sure you \
                                              want to overwrite it?",
                                              _Qtui.QMessageBox.Yes |\
                                              _Qtui.QMessageBox.No, 
                                              _Qtui.QMessageBox.No):
                return
            for i in self.reflist:
                if i.initkey == key:
                    self.delete_Row(i)
                    break
        self.dictionary[key] = value
        if key != oldkey:
            try:
                del self.dictionary["oldkey"]
            except KeyError:
                pass
        row.saveApproved()
    
    @_Qt.pyqtSlot(bool)
    def setEditable(self, boolean):
        self.editable = boolean
        for i in self.reflist:
            i.setEditable(boolean)
        if boolean:
            self.lastrow = _Row("","")
            self.layout.addWidget(self.lastrow)
            self.lastrow.changeSaved.connect(self.newlastrow)
            self.lastrow.changeSaved.connect(self.writeToDict)
            self.lastrow.deleted.connect(self.delete_Row)
        else:
            try:
                self.layout.removeWidget(self.lastrow)
                self.lastrow.hide()
                del self.lastrow
            except AttributeError:
                pass
              
if __name__ == "__main__":
    import sys
    app = _Qtui.QApplication(sys.argv)
    a = DictEditor({1:"Test","2":"MoreTest","3":"LastTest"})
    #To enable showing the underlying dictionary:
    b = a.actionsmenu.addAction("Print Dict", lambda:print(a.dictionary))
    a.show()
    app.exec_()