import re

from qgis.PyQt import QtGui, QtWidgets
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsProject,QgsUnitTypes

class LayoutList():
    def __init__(self,parent=None):
        """Initialize the layout list"""
        self.parent = parent
        self.layout_list = None
        
        QgsProject.instance().layoutManager().layoutAdded.connect(self.updateLayoutWidgetList)
        QgsProject.instance().layoutManager().layoutRemoved.connect(self.updateLayoutWidgetList)
        QgsProject.instance().layoutManager().layoutRenamed.connect(self.updateLayoutWidgetList)
        
        self.updateLayoutWidgetList()
        
    def updateLayoutWidgetList(self):
        """Generate the list of layouts"""
        layout_manager= self.parent.project.getLayoutManager()
        self.layout_list = layout_manager.layouts()
        self.parent.listWidget.clear()
        search_value = self.parent.mLineEdit.value().replace("*", r"\*").replace("+", r"\+").replace("(", r"\(")\
            .replace(")",r"\)").replace("?", r"\?").replace("[", r"\[").replace("]", r"\]")
        
        for layout in self.layout_list:
            # necessary to ensure that tooltips are updated when layout format or page count changes
            layout.pageCollection().changed.connect(self.updateLayoutWidgetList)
            match = bool(re.search(search_value, layout.name(), re.IGNORECASE))
            if match:
                layout = layout_manager.layoutByName(layout.name())
                layout_page_collection = layout.pageCollection()
                page_count = layout_page_collection.pageCount()
                if layout_page_collection.hasUniformPageSizes():
                    page_size = layout_page_collection.maximumPageSize()
                    units = QgsUnitTypes.encodeUnit(layout.units())
                    page_size_text = f'{page_size.width()}x{page_size.height()} {units}'
                else:
                    page_size_text = 'variable'

                item = QtWidgets.QListWidgetItem()
                item.setText(layout.name())
                item.setIcon(QtGui.QIcon(':/plugins/layout_panel/icons/mIconLayout.svg'))
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                item.setToolTip(f'Page Count: {page_count} <br> Page Size: {page_size_text}')
                self.parent.listWidget.addItem(item)
        
        #Disable delete button if there are no layouts in the list
        if len(self.layout_list) == 0:
            self.parent.pbDeleteLayout.setEnabled(False)
        else:
            self.parent.pbDeleteLayout.setEnabled(True)
    
    