import math

from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import QEvent, QObject, Qt, QTimer
from qgis.core import QgsApplication, QgsPrintLayout, QgsProject, QgsUnitTypes
from .i18n import tr
from .icons import icon
from .signal_relay import SignalRelay

# Layouts are grouped in folders by the "/" in their names: "Maps/North/Plan 1"
# is the layout "Plan 1" in the folder "North" of the folder "Maps".
# The QGIS layout manager has no folders, so folders only exist in the panel.
LAYOUT_NAME_ROLE = Qt.ItemDataRole.UserRole
FOLDER_PATH_ROLE = Qt.ItemDataRole.UserRole + 1


def splitName(name):
    """Return the parts of a layout name split on "/", without empty parts"""
    parts = [part.strip() for part in name.split('/')]
    parts = [part for part in parts if part]
    return parts or [name]


def joinName(parts):
    return '/'.join(parts)


def folderParts(name):
    """Return the folder parts of a layout name"""
    return splitName(name)[:-1]


class TreeItem(QtWidgets.QTreeWidgetItem):
    """Tree item sorted with folders first, then by name"""

    def isFolder(self):
        return self.data(0, FOLDER_PATH_ROLE) is not None

    def __lt__(self, other):
        if self.isFolder() != other.isFolder():
            return self.isFolder()
        return self.text(0).casefold() < other.text(0).casefold()


class RenameDelegate(QtWidgets.QStyledItemDelegate):
    """Edit the full name (with its folders) instead of the displayed short name.

    The rename is done by LayoutItem when the editor closes, so nothing is
    written back to the item.
    """

    def setEditorData(self, editor, index):
        full_name = index.data(LAYOUT_NAME_ROLE)
        if full_name is None:
            full_name = index.data(FOLDER_PATH_ROLE)
        editor.setText(full_name)

    def setModelData(self, editor, model, index):
        pass


class DropHandler(QObject):
    """Move the layouts and folders dropped in the tree to the target folder"""

    def __init__(self, layout_list):
        super().__init__(layout_list.tree)
        self.layout_list = layout_list

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Drop and event.source() is self.layout_list.tree:
            tree = self.layout_list.tree
            target_item = tree.itemAt(event.position().toPoint() if hasattr(event, 'position') else event.pos())
            indicator = tree.dropIndicatorPosition()
            if target_item is None:
                target_folder = []
            elif target_item.isFolder() and indicator == QtWidgets.QAbstractItemView.DropIndicatorPosition.OnItem:
                target_folder = splitName(target_item.data(0, FOLDER_PATH_ROLE))
            else:
                target_folder = self.layout_list.itemFolder(target_item)
            items = tree.selectedItems()
            # Ignore the drop so Qt does not move the items itself: the tree is
            # rebuilt from the new layout names once the drag is over
            event.setDropAction(Qt.DropAction.IgnoreAction)
            event.accept()
            moves = self.layout_list.moveItems(items, target_folder)
            QTimer.singleShot(0, lambda: self.layout_list.renameLayouts(moves))
            return True
        return False


class LayoutList():
    def __init__(self,parent=None):
        """Initialize the layout list"""
        self.parent = parent
        self.tree = parent.listWidget
        # Paths of the folders the user collapsed, to keep them collapsed when the list is refreshed
        self.collapsed_folders = set()
        self.updating = False

        self.tree.setHeaderHidden(True)
        self.tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.tree.setItemDelegate(RenameDelegate(self.tree))
        self.tree.itemExpanded.connect(lambda item: self.folderToggled(item, True))
        self.tree.itemCollapsed.connect(lambda item: self.folderToggled(item, False))

        # Drag and drop moves layouts and folders to another folder
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.drop_handler = DropHandler(self)
        self.tree.viewport().installEventFilter(self.drop_handler)

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
        self.tree.viewport().removeEventFilter(self.drop_handler)
        self.relay.delete()


    def updateLayoutList(self):
        """Generate the tree of layouts"""
        self.updating = True
        self.tree.clear()
        layout_manager=self.parent.project.getLayoutManager()
        layouts = layout_manager.layouts()
        search_value = self.parent.mLineEdit.value().lower()
        folders = {}

        for layout in layouts:
            # Reports (QgsReport) have no page collection of their own
            is_print_layout = isinstance(layout, QgsPrintLayout)
            if is_print_layout:
                self.relay.watch(layout.pageCollection().changed)
            if search_value not in layout.name().lower():
                continue

            parts = splitName(layout.name())
            item = TreeItem(self.folderItem(parts[:-1], folders))
            item.setText(0, parts[-1])
            item.setData(0, LAYOUT_NAME_ROLE, layout.name())
            item.setFlags((item.flags() | Qt.ItemFlag.ItemIsEditable) & ~Qt.ItemFlag.ItemIsDropEnabled)
            if is_print_layout:
                item.setIcon(0, icon('mIconLayout.svg'))
                item.setToolTip(0, self.layoutToolTip(layout))
            else:
                item.setIcon(0, QgsApplication.getThemeIcon('/mIconReport.svg'))
                item.setToolTip(0, tr('Report'))

        for path, folder in folders.items():
            folder.setToolTip(0, tr('Layout Count: {count}').format(count=len(self.layoutNames([folder]))))
            # Show the search results in collapsed folders too
            folder.setExpanded(bool(search_value) or path not in self.collapsed_folders)
        # Without folders, no space is kept for the expand arrows
        self.tree.setRootIsDecorated(bool(folders))
        self.updating = False

        #Disable delete button if there are no layouts in the list
        if len(layouts) == 0:
            self.parent.pbDeleteLayout.setEnabled(False)
        else:
            self.parent.pbDeleteLayout.setEnabled(True)


    def folderItem(self, parts, folders):
        """Return the item of a folder, creating it and its parent folders if needed

        :param parts: the folder parts; the tree itself for the root folder
        :param folders: {folder path: folder item} of the folders created so far
        """
        if not parts:
            return self.tree
        path = joinName(parts)
        if path not in folders:
            folder = TreeItem(self.folderItem(parts[:-1], folders))
            folder.setText(0, parts[-1])
            folder.setData(0, FOLDER_PATH_ROLE, path)
            folder.setIcon(0, icon('mIconFolder.svg'))
            folder.setFlags(folder.flags() | Qt.ItemFlag.ItemIsEditable)
            folders[path] = folder
        return folders[path]


    def folderToggled(self, item, expanded):
        """Remember the folders the user collapsed"""
        if self.updating or self.parent.mLineEdit.value():
            return
        path = item.data(0, FOLDER_PATH_ROLE)
        if expanded:
            self.collapsed_folders.discard(path)
        else:
            self.collapsed_folders.add(path)


    @staticmethod
    def layoutName(item):
        """Return the full name of the layout of an item, or None for a folder"""
        return item.data(0, LAYOUT_NAME_ROLE)


    def itemFolder(self, item):
        """Return the parts of the folder containing an item"""
        parent = item.parent()
        return splitName(parent.data(0, FOLDER_PATH_ROLE)) if parent else []


    def layoutNames(self, items):
        """Return the names of the layouts of the items, with the layouts of the folders among them"""
        names = []

        def add(item):
            name = self.layoutName(item)
            if name is not None:
                if name not in names:
                    names.append(name)
            else:
                for index in range(item.childCount()):
                    add(item.child(index))

        for item in items:
            add(item)
        return names


    def selectedLayoutNames(self):
        """Return the names of the selected layouts, with the layouts of the selected folders"""
        return self.layoutNames(self.tree.selectedItems())


    def allLayoutNames(self):
        """Return the names of all the layouts shown in the list"""
        root = self.tree.invisibleRootItem()
        return self.layoutNames([root.child(index) for index in range(root.childCount())])


    def moveItems(self, items, target_folder):
        """Return the renames moving layouts and folders into a folder

        :param items: the layout and folder items to move
        :param target_folder: the parts of the destination folder
        :returns: list of (old name, new name)
        """
        moves = []
        for item in items:
            name = self.layoutName(item)
            if name is not None:
                moves.append((name, joinName(target_folder + [splitName(name)[-1]])))
                continue
            folder = splitName(item.data(0, FOLDER_PATH_ROLE))
            if target_folder[:len(folder)] == folder:
                continue  # into itself or one of its subfolders
            new_folder = target_folder + [folder[-1]]
            for name in self.layoutNames([item]):
                moves.append((name, joinName(new_folder + splitName(name)[len(folder):])))
        # A layout selected with its folder is moved with the folder
        renames = {}
        for old_name, new_name in moves:
            renames.setdefault(old_name, new_name)
        return [(old_name, new_name) for old_name, new_name in renames.items() if old_name != new_name]


    def renameFolder(self, old_path, new_path):
        """Rename a folder by renaming all its layouts"""
        old_folder = splitName(old_path)
        new_folder = splitName(new_path)
        # Layouts hidden by the search are renamed too
        layout_names = [layout.name() for layout in self.parent.project.getLayoutManager().layouts()]
        moves = [(name, joinName(new_folder + splitName(name)[len(old_folder):]))
                 for name in layout_names if folderParts(name)[:len(old_folder)] == old_folder]
        if old_path in self.collapsed_folders:
            self.collapsed_folders.add(joinName(new_folder))
        return self.renameLayouts(moves)


    def renameLayouts(self, renames):
        """Rename layouts, only if none of the new names is already used

        :param renames: list of (old name, new name)
        :returns: True if the layouts were renamed
        """
        renames = [(old_name, new_name) for old_name, new_name in renames if old_name != new_name]
        if not renames:
            return True
        layout_manager = self.parent.project.getLayoutManager()
        old_names = {old_name for old_name, _ in renames}
        new_names = [new_name for _, new_name in renames]
        taken = {layout.name() for layout in layout_manager.layouts()} - old_names
        if len(set(new_names)) != len(new_names) or taken.intersection(new_names):
            self.parent.iface.messageBar().pushWarning(tr('Failed to rename layout'), ' ' + tr('Entered layout name already exists or is invalid.'))
            self.updateLayoutList()
            return False
        layouts = [(layout_manager.layoutByName(old_name), new_name) for old_name, new_name in renames]
        # Two passes so layouts can swap names
        for index, (layout, _) in enumerate(layouts):
            layout.setName(f'__layout_panel_rename_{index}__')
        for layout, new_name in layouts:
            layout.setName(new_name)
        return True


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
        """Duplicate one or multiple selected layouts, with the layouts of the selected folders"""
        # Copy the list of selected layouts to avoid race condition due to refresh
        for layout_name in self.selectedLayoutNames():
            self.parent.layout_item.duplicateLayout(layout_name)


    def removeSelectedLayouts(self, askConfirmation=True):
        """Remove one or multiple selected layouts, with the layouts of the selected folders"""
        selected_items = self.tree.selectedItems()
        layout_names = self.selectedLayoutNames()
        if not layout_names:
            return
        if askConfirmation:
            qm = QtWidgets.QMessageBox
            if len(selected_items) == 1 and selected_items[0].isFolder():
                ret = qm.question(self.parent, tr('Remove Folder'),
                                tr('Are you sure you want to remove permanently the folder "{name}" and its {count} layouts?').format(
                                    name=selected_items[0].data(0, FOLDER_PATH_ROLE), count=len(layout_names)),
                                qm.StandardButton.Yes | qm.StandardButton.No)
            elif len(layout_names) == 1:
                ret = qm.question(self.parent, tr('Remove Selected Layout'),
                                tr('Are you sure you want to remove permanently "{name}" ?').format(name=layout_names[0]), qm.StandardButton.Yes | qm.StandardButton.No)
            else:
                ret = qm.question(self.parent, tr('Remove Selected Layouts'),
                                tr('Are you sure you want to remove permanently {count} layouts?').format(count=len(layout_names)), qm.StandardButton.Yes | qm.StandardButton.No)

            if ret == qm.StandardButton.No:
                return

        for layout_name in layout_names:
            self.parent.layout_item.removeLayout(layout_name)
