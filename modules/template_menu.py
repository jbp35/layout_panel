import os

from qgis.PyQt import QtGui, QtWidgets
from qgis.PyQt.QtCore import QDir, QUrl,QFileInfo,  QSettings
from qgis.core import QgsApplication



class TemplateMenu():
    def __init__(self,parent=None):
        """Initialize the template menu"""
        self.parent = parent
        
        self.template_menu=QtWidgets.QMenu()
        self.parent.tbTemplateMenu.setMenu(self.template_menu)
        self.template_menu.aboutToShow.connect(self.updateTemplateMenu)
        self.template_menu.triggered.connect(self.templateMenuTriggered)
        
        
    def updateTemplateMenu(self):
        """Generate the template menu"""
        
        # clear the template menu first
        for action in self.template_menu.actions():
            self.template_menu.removeAction(action)
        
        searchPathsForTemplates=QSettings().value("core/Layout/searchPathsForTemplates")
        searchPathsForTemplates.append(QgsApplication.qgisSettingsDirPath()+'composer_templates')
        searchPathsForTemplates.append(os.path.dirname(os.path.realpath(__file__)) + '/templates')

        layoutTemplateList = []
        
        for path in searchPathsForTemplates:
            projectTemplateDir = QDir(path)
            projectTemplateDir.setFilter(QDir.Files)
            projectTemplateDir.setNameFilters(["*.qpt", "*.QPT"])
            projectTemplateDir.setSorting(QDir.Time)
            
            for template in projectTemplateDir.entryList():
                layoutTemplateList.append(projectTemplateDir.filePath(template))

        if not layoutTemplateList:
            layoutTemplateAction = self.template_menu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionNewLayout.svg"), 'Template folder is empty')
            layoutTemplateAction.setEnabled(False)
        actions = []
        for layoutTemplatePath in layoutTemplateList:
            layoutTemplateAction = QtWidgets.QAction(QFileInfo(layoutTemplatePath).baseName(), self.parent)
            layoutTemplateAction.setIcon(QtGui.QIcon(":/plugins/layout_panel/icons/mActionNewLayoutFromTemplate.svg"))
            layoutTemplateAction.setData(["layoutTemplateAction",layoutTemplatePath])
            actions.append(layoutTemplateAction)
        self.template_menu.addActions(actions)
        self.template_menu.addSeparator()
        selectTemplateAction = self.template_menu.addAction("Choose Another Template File...")
        selectTemplateAction.setData(["selectTemplateAction", projectTemplateDir.absolutePath()])
        openTemplateFolderAction = self.template_menu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mIconFolder.svg"), "Open Template Folder")
        openTemplateFolderAction.setData(["openTemplateFolderAction", projectTemplateDir.absolutePath()])
        

    def templateMenuTriggered(self, layoutTemplateAction):
        """Called when template menu is triggered"""
        if layoutTemplateAction.data()[0] == "openTemplateFolderAction":
            QtGui.QDesktopServices.openUrl(QUrl.fromLocalFile(layoutTemplateAction.data()[1]))
        elif layoutTemplateAction.data()[0] == "selectTemplateAction":
            fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Choose a template to create a new layout', layoutTemplateAction.data()[1], 'Layout templates (*.qpt *.QPT)')
            if fname[0] != '':
                self.parent.layou_item.createLayoutFromTemplate(fname[0])
        elif layoutTemplateAction.data()[0] == "layoutTemplateAction":
            self.parent.layout_item.createLayoutFromTemplate(layoutTemplateAction.data()[1])

