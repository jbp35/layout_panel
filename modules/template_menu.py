from qgis.PyQt import QtGui, QtWidgets
from qgis.PyQt.QtCore import QDir, QUrl,QFileInfo



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
        
        search_paths_for_templates=self.parent.project.getSearchPathsForTemplates()
        layout_template_list = []

        # list template files in each directory
        for path in search_paths_for_templates:
            template_dir = QDir(path)
            template_dir.setFilter(QDir.Files)
            template_dir.setNameFilters(["*.qpt", "*.QPT"])
            template_dir.setSorting(QDir.Time)
            
            for template in template_dir.entryList():
                layout_template_list.append(template_dir.filePath(template))

        #if there is no templates to display show a message
        if not layout_template_list:
            layoutTemplateAction = self.template_menu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionNewLayout.svg"), 'Template folder is empty')
            layoutTemplateAction.setEnabled(False)
        
        #add menu action for each template file found
        actions_list = []
        for layout_template_path in layout_template_list:
            layout_template_action = QtWidgets.QAction(QFileInfo(layout_template_path).baseName(), self.parent)
            layout_template_action.setIcon(QtGui.QIcon(":/plugins/layout_panel/icons/mActionNewLayoutFromTemplate.svg"))
            layout_template_action.setData(["layoutTemplateAction", layout_template_path])
            actions_list.append(layout_template_action)
        self.template_menu.addActions(actions_list)
        
        
        self.template_menu.addSeparator()
        selectTemplateAction = self.template_menu.addAction("Choose Another Template File...")
        selectTemplateAction.setData(["selectTemplateAction"])
        #TODO: add settings icon
        editTemplatePathsAction = self.template_menu.addAction("Layout Templates Settings...")
        editTemplatePathsAction.setData(["editTemplatePaths"])
        openTemplateFolderAction = self.template_menu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mIconFolder.svg"), "Open Default Template Folder")
        openTemplateFolderAction.setData(["openTemplateFolderAction", search_paths_for_templates[0]])
        

    def templateMenuTriggered(self, layoutTemplateAction):
        """Called when template menu is triggered"""
        if layoutTemplateAction.data()[0] == "openTemplateFolderAction":
            QtGui.QDesktopServices.openUrl(QUrl.fromLocalFile(layoutTemplateAction.data()[1]))
        
        elif layoutTemplateAction.data()[0] == "selectTemplateAction":
            fname = QtWidgets.QFileDialog.getOpenFileName(self.parent, 'Choose a template to create a new layout', self.parent.project.getLastUsedFolder(), 'Layout templates (*.qpt *.QPT)')
            if fname[0] != '':
                self.parent.project.createLayoutFromTemplate(fname[0])
        
        elif layoutTemplateAction.data()[0] == "layoutTemplateAction":
            self.parent.project.createLayoutFromTemplate(layoutTemplateAction.data()[1])
            
        elif layoutTemplateAction.data()[0] == "editTemplatePaths":
            self.parent.iface.showOptionsDialog(currentPage = "Layouts")

