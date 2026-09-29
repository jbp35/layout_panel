import math

from qgis.PyQt import QtWidgets, sip
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsApplication, QgsPrintLayout, QgsProject, QgsUnitTypes
from .icons import icon

class LayoutList():
    def __init__(self,parent=None):
        """Initialize the layout list"""
        self.parent = parent
        # Page collections whose changed signal is connected, to connect each only once
        self.watched_page_collections = []

        layout_manager = QgsProject.instance().layoutManager()
        layout_manager.layoutAdded.connect(self.updateLayoutList)
        layout_manager.layoutRemoved.connect(self.updateLayoutList)
        layout_manager.layoutRenamed.connect(self.updateLayoutList)

        self.updateLayoutList()


    def cleanup(self):
        """Disconnect from QGIS signals when the plugin is unloaded"""
        layout_manager = QgsProject.instance().layoutManager()
        layout_manager.layoutAdded.disconnect(self.updateLayoutList)
        layout_manager.layoutRemoved.disconnect(self.updateLayoutList)
        layout_manager.layoutRenamed.disconnect(self.updateLayoutList)
        for page_collection in self.watched_page_collections:
            try:
                page_collection.changed.disconnect(self.updateLayoutList)
            except (RuntimeError, TypeError):
                # the layout has been deleted in the meantime
                pass
        self.watched_page_collections = []
       
        
    def updateLayoutList(self):
        """Generate the list of layouts"""
        self.parent.listWidget.clear()
        layout_manager=self.parent.project.getLayoutManager()
        layouts = layout_manager.layouts()
        # forget page collections of layouts deleted since the last refresh
        self.watched_page_collections = [page_collection for page_collection in self.watched_page_collections
                                         if not sip.isdeleted(page_collection)]
        search_value = self.parent.mLineEdit.value().lower()

        for layout in layouts:
            # Reports (QgsReport) have no page collection of their own
            is_print_layout = isinstance(layout, QgsPrintLayout)
            if is_print_layout:
                self.watchPageCollection(layout.pageCollection())
            if search_value not in layout.name().lower():
                continue

            item = QtWidgets.QListWidgetItem()
            item.setText(layout.name())
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            if is_print_layout:
                item.setIcon(icon('mIconLayout.svg'))
                item.setToolTip(self.layoutToolTip(layout))
            else:
                item.setIcon(QgsApplication.getThemeIcon('/mIconReport.svg'))
                item.setToolTip('Report')
            self.parent.listWidget.addItem(item)
        
        #Disable delete button if there are no layouts in the list
        if len(layouts) == 0:
            self.parent.pbDeleteLayout.setEnabled(False)
        else:
            self.parent.pbDeleteLayout.setEnabled(True)


    def watchPageCollection(self, page_collection):
        """Refresh the list when page count or size changes, to keep tooltips up to date"""
        if any(page_collection is watched for watched in self.watched_page_collections):
            return
        page_collection.changed.connect(self.updateLayoutList)
        self.watched_page_collections.append(page_collection)


    @staticmethod
    def layoutToolTip(layout):
        """Return the tooltip describing a print layout"""
        layout_page_collection = layout.pageCollection()
        page_count = layout_page_collection.pageCount()

        if layout_page_collection.hasUniformPageSizes():
            page_size = layout_page_collection.maximumPageSize()
            units = QgsUnitTypes.encodeUnit(layout.units())
            page_size_text = f'{page_size.width()}x{page_size.height()} {units}'
        else:
            page_size_text = 'variable'

        # The scale is NaN or infinite when the map has an empty extent
        map_scale = 'Unknown'
        reference_map = layout.referenceMap()
        if reference_map and math.isfinite(reference_map.scale()):
            map_scale = f'1:{round(reference_map.scale())}'

        return f'Page Count: {page_count} <br> Page Size: {page_size_text} <br> Map Scale: {map_scale}'

            
    def duplicateSelectedLayouts(self):
        """Duplicate one or multiple selected layouts"""
        selected_items = self.parent.listWidget.selectedItems()
        
        # Copy the list of selected items to avoid race condition due to refresh
        list_layout_names = []  
        for layout_item in selected_items:
            list_layout_names.append(layout_item.text())
        for layout_name in list_layout_names:
            self.parent.layout_item.duplicateLayout(layout_name)


    def removeSelectedLayouts(self, askConfirmation=True):
        """Remove one or multiple selected layouts"""
        selected_items = self.parent.listWidget.selectedItems()
        if askConfirmation:
            qm = QtWidgets.QMessageBox
            if len(selected_items) == 0:
                return
            elif len(selected_items) == 1:
                ret = qm.question(self.parent, 'Remove Selected Layout',
                                f'Are you sure you want to remove permanently "{selected_items[0].text()}" ?', qm.StandardButton.Yes | qm.StandardButton.No)
            else:
                ret = qm.question(self.parent, 'Remove Selected Layouts',
                                f'Are you sure you want to remove permanently {len(selected_items)} layouts?', qm.StandardButton.Yes | qm.StandardButton.No)
        
            if ret == qm.StandardButton.No:
                return
            
        layout_names = []
        for item in selected_items:
            layout_names.append(item.text())
        for layout_name in layout_names:
            self.parent.layout_item.removeLayout(layout_name)
    
    