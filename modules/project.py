from qgis.PyQt.QtCore import QDir, QFileInfo
from qgis.core import QgsProject, QgsSettings


class Project():
    def __init__(self,parent=None):
        """Initialize qgis project"""
        self.parent = parent
        self.project_instance = None
        self.project_layout_manager = None
        self.last_used_folder = None
        
        QgsProject.instance().readProject.connect(self.updateProjectInstance)
        QgsProject.instance().cleared.connect(self.updateProjectInstance)
        
        self.updateProjectInstance()
        
    def updateProjectInstance(self):
        """Update project instance and project layout manager"""
        self.parent.mLineEdit.clearValue()
        self.project_instance = QgsProject.instance()
        self.project_layout_manager = self.project_instance.layoutManager()
        
        last_layout_export_dir = QgsSettings().value('APP/lastLayoutExportDir')
        if last_layout_export_dir == "":
            self.last_used_folder = QDir(self.project_instance.homePath()).path()
        else:
            self.last_used_folder = QFileInfo(last_layout_export_dir).dir()
            
        
    def getLayoutManager(self):
        return self.project_layout_manager
    
    def getProjectInstance(self):
        return self.project_instance
    
    def getLastUsedFolder(self):
        return self.last_used_folder
    
    def setLastExportDir(self, path):
        if not path or path=='': return
        if not QFileInfo(path).isDir():
            path=QFileInfo(path).dir().absolutePath()
        QgsSettings().setValue('APP/lastLayoutExportDir', path)
        self.last_used_folder = path