from qgis.PyQt.QtCore import QDir
from qgis.core import QgsProject, QgsApplication

class Project():
    def __init__(self,parent=None):
        """Initialize qgis project"""
        self.parent = parent
        self.project_instance = None
        self.project_layout_manager = None
        
        QgsProject.instance().readProject.connect(self.updateProjectInstance)
        QgsProject.instance().cleared.connect(self.updateProjectInstance)
        
        self.updateProjectInstance()
        
    def updateProjectInstance(self):
        """Update project instance and project layout manager"""
        self.template_dir = QDir(QgsApplication.qgisSettingsDirPath() + '/composer_templates')
        self.parent.mLineEdit.clearValue()
        self.project_instance = QgsProject.instance()
        self.project_layout_manager = self.project_instance.layoutManager()
        
    def getLayoutManager(self):
        return self.project_layout_manager
    
    def getProjectInstance(self):
        return self.project_instance
