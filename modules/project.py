import os

from qgis.PyQt.QtCore import QDir, QFileInfo,  QSettings
from qgis.core import QgsApplication, QgsProject, QgsPrintLayout,QgsSettings,QgsReadWriteContext
from qgis.PyQt import QtXml

class Project():
    def __init__(self,plugin_dir,parent=None):
        """Initialize qgis project"""
        self.parent = parent
        self.project_instance = None
        self.project_layout_manager = None
        self.last_used_folder = None
        self.plugin_dir=plugin_dir
        
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
            self.last_used_folder = QDir(self.project_instance.homePath()).absolutePath()
        else:
            self.last_used_folder = QFileInfo(last_layout_export_dir).dir().absolutePath()
            
        
    def getLayoutManager(self):
        """Return currrent layout manager"""
        return self.project_layout_manager
    
    
    def getProjectInstance(self):
        """Return current project instance"""
        return self.project_instance
    
    
    def getLastUsedFolder(self):
        """Return last used folder"""
        return self.last_used_folder
    
    
    def setLastExportDir(self, path):
        """Set last export directory"""
        if not path or path=='': return
        if not QFileInfo(path).isDir():
            path=QFileInfo(path).dir().absolutePath()
        QgsSettings().setValue('APP/lastLayoutExportDir', path)
        self.last_used_folder = path
        
        
    def getSearchPathsForTemplates(self):
        """return a list a path to search for templates"""
        searchPathsForTemplates=[]
        
        #add default path
        searchPathsForTemplates.append(self.getDefaultTemplateFolderPath())
        
        #add layout panel template folder
        searchPathsForTemplates.append(self.plugin_dir + '/templates')
      
        #add additional paths
        additional_path_list=QSettings().value("core/Layout/searchPathsForTemplates")
        if additional_path_list:
            for path in additional_path_list:
                searchPathsForTemplates.append(path)
            
        return searchPathsForTemplates
    
    
    def getDefaultTemplateFolderPath(self):
        """return default folder for layout templates"""
        return QgsApplication.qgisSettingsDirPath()+'composer_templates'
        
        
    def createNewLayout(self):
        """Create a new blank layout"""
        iterator = 1
        while True:
            if self.project_layout_manager.layoutByName('Layout ' + str(iterator)) is None:
                layout_name = "Layout " + str(iterator)
                layout = QgsPrintLayout(self.parent.project.getProjectInstance())
                layout.initializeDefaults()
                layout.setName(layout_name)
                self.project_layout_manager.addLayout(layout)
                return
            iterator = iterator + 1


    def createLayoutFromTemplate(self, layout_template_path):
        """Create a new layout based on a template file"""
        document = QtXml.QDomDocument()
        with open(layout_template_path) as file:
            content = file.read()
        document.setContent(content)
        template_name = QFileInfo(layout_template_path).baseName()
        iterator = 1
        while True:
            if self.project_layout_manager.layoutByName(template_name + ' ' + str(iterator)) is None :
                layout = QgsPrintLayout(self.project_instance)
                layout_name = template_name + ' ' + str(iterator)
                layout.loadFromTemplate(document, QgsReadWriteContext())
                layout.setName(layout_name)
                self.project_layout_manager.addLayout(layout)
                return
            iterator = iterator + 1
