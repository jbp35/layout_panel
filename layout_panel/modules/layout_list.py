import math

from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsApplication, QgsPrintLayout, QgsProject, QgsUnitTypes
from .i18n import tr
from .icons import icon
from .signal_relay import SignalRelay

class LayoutList():
    def __init__(self,parent=None):
        """Initialize the layout list"""
        self.parent = parent
        # Refreshes the list; also watches each layout's page collection so
        # tooltips stay up to date when page count or size changes
        self.relay = SignalRelay(self.updateLayoutList, parent)

        layout_manager = QgsProject.instance().layoutManager()
        self.relay.watch(layout_manager.layoutAdded)
        self.relay.watch(layout_manager.layoutRemoved)
        self.relay.watch(layout_manager.layoutRenamed)

        self.updateLayoutList()


    def cleanup(self):
        """Disconnect from QGIS signals when the plugin is unloaded"""
        self.relay.delete()


    def updateLayoutList(self):
        """Generate the list of layouts"""
        self.parent.listWidget.clear()
        layout_manager=self.parent.project.getLayoutManager()
        layouts = layout_manager.layouts()
        search_value = self.parent.mLineEdit.value().lower()

        for layout in layouts:
            # Reports (QgsReport) have no page collection of their own
            is_print_layout = isinstance(layout, QgsPrintLayout)
            if is_print_layout:
                self.relay.watch(layout.pageCollection().changed)
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
                item.setToolTip(tr('Report'))
            self.parent.listWidget.addItem(item)
        
        #Disable delete button if there are no layouts in the list
        if len(layouts) == 0:
            self.parent.pbDeleteLayout.setEnabled(False)
        else:
            self.parent.pbDeleteLayout.setEnabled(True)


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
            page_size_text = tr('variable')

        # The scale is NaN or infinite when the map has an empty extent
        map_scale = tr('Unknown')
        reference_map = layout.referenceMap()
        if reference_map and math.isfinite(reference_map.scale()):
            map_scale = f'1:{round(reference_map.scale())}'

        return ' <br> '.join([tr('Page Count: {count}').format(count=page_count),
                             tr('Page Size: {size}').format(size=page_size_text),
                             tr('Map Scale: {scale}').format(scale=map_scale)])

            
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
                ret = qm.question(self.parent, tr('Remove Selected Layout'),
                                tr('Are you sure you want to remove permanently "{name}" ?').format(name=selected_items[0].text()), qm.StandardButton.Yes | qm.StandardButton.No)
            else:
                ret = qm.question(self.parent, tr('Remove Selected Layouts'),
                                tr('Are you sure you want to remove permanently {count} layouts?').format(count=len(selected_items)), qm.StandardButton.Yes | qm.StandardButton.No)
        
            if ret == qm.StandardButton.No:
                return
            
        layout_names = []
        for item in selected_items:
            layout_names.append(item.text())
        for layout_name in layout_names:
            self.parent.layout_item.removeLayout(layout_name)
    
    