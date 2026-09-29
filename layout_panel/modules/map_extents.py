from qgis.PyQt import sip
from qgis.PyQt.QtCore import QObject, QPointF, QRectF, Qt
from qgis.PyQt.QtGui import QAction, QBrush, QColor, QCursor, QFont, QPainterPath, QPen, QPolygonF
from qgis.core import (QgsCoordinateTransform, QgsCsException, QgsGeometry, QgsLayoutItemMap,
                       QgsPointXY, QgsProject, QgsRectangle)
from qgis.gui import QgsMapCanvasItem, QgsMapToolPan

from .icons import icon
from .signal_relay import SignalRelay

LINE_COLOR = QColor('#3388ff')
FILL_COLOR = QColor(51, 136, 255, 40)
HIGHLIGHT_FILL_COLOR = QColor(51, 136, 255, 110)
# a press and release closer than this (in pixels) is a click, not a pan
CLICK_TOLERANCE = 4
HANDLE_RADIUS = 8


class MapExtentsItem(QgsMapCanvasItem):
    """Canvas item drawing the extent of every map item of every print layout,
    labelled with the layout name, with a handle in the center to move it"""

    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        # (layout name, map uuid) of the extent under the cursor
        # (names and ids, not objects: QGIS may delete them)
        self.highlighted = None
        # (layout name, map uuid) of the extent being moved and its offset in pixels
        self.dragged = None
        self.drag_offset = QPointF()
        self.setZValue(1000)

    def extents(self):
        """Return (layout, map item, label, polygon in canvas CRS) for each layout map"""
        extents = []
        destination_crs = self.canvas.mapSettings().destinationCrs()
        for layout in QgsProject.instance().layoutManager().printLayouts():
            maps = [item for item in layout.items() if isinstance(item, QgsLayoutItemMap)]
            for map_item in maps:
                label = layout.name() if len(maps) == 1 else f'{layout.name()} - {map_item.displayName()}'
                geometry = QgsGeometry.fromQPolygonF(map_item.visibleExtentPolygon())
                if geometry.isEmpty():
                    continue
                if map_item.crs().isValid() and destination_crs.isValid() and map_item.crs() != destination_crs:
                    try:
                        geometry.transform(QgsCoordinateTransform(map_item.crs(), destination_crs, QgsProject.instance()))
                    except QgsCsException:
                        continue
                extents.append((layout, map_item, label, geometry))
        return extents

    def extentAt(self, map_point):
        """Return (layout, map item) of the map extent containing the point, preferring the smallest extent"""
        point = QgsGeometry.fromPointXY(map_point)
        hits = [(geometry.area(), layout, map_item) for layout, map_item, _, geometry in self.extents()
                if geometry.contains(point)]
        if not hits:
            return None
        _, layout, map_item = min(hits, key=lambda hit: hit[0])
        return layout, map_item

    def layoutAt(self, map_point):
        """Return the layout of the map extent containing the point"""
        hit = self.extentAt(map_point)
        return hit[0] if hit else None

    def handlePosition(self, geometry):
        """Pixel position of the move handle of an extent"""
        return self.toCanvasCoordinates(geometry.centroid().asPoint())

    def pixelPolygon(self, geometry):
        """The extent polygon in canvas pixels"""
        return QPolygonF([self.toCanvasCoordinates(QgsPointXY(vertex.x(), vertex.y())) for vertex in geometry.vertices()])

    @staticmethod
    def hasHandle(layout, map_item, pixel_polygon):
        """Extents too small on screen get no handle: zoom in to move them"""
        rect = pixel_polygon.boundingRect()
        return movable(layout, map_item) and min(rect.width(), rect.height()) >= HANDLE_RADIUS * 5

    def handleAt(self, position):
        """Return (layout, map item, center in canvas CRS) of the move handle under the pixel position"""
        for layout, map_item, _, geometry in self.extents():
            if not self.hasHandle(layout, map_item, self.pixelPolygon(geometry)):
                continue
            offset = self.handlePosition(geometry) - QPointF(position)
            if offset.manhattanLength() <= HANDLE_RADIUS * 2:
                return layout, map_item, geometry.centroid().asPoint()
        return None

    def boundingRect(self):
        return QRectF(0, 0, self.canvas.width(), self.canvas.height())

    def updatePosition(self):
        # the item always covers the whole canvas and draws in screen coordinates
        self.setPos(0, 0)
        self.prepareGeometryChange()

    def paint(self, painter, option=None, widget=None):
        font = QFont(painter.font())
        font.setBold(True)
        painter.setFont(font)
        painter.setRenderHint(painter.RenderHint.Antialiasing)
        metrics = painter.fontMetrics()

        # draw the highlighted extent last so it stays on top
        extents = []
        for layout, map_item, label, geometry in self.extents():
            key = (layout.name(), map_item.uuid())
            offset = self.drag_offset if self.dragged == key else QPointF()
            polygon = self.pixelPolygon(geometry).translated(offset)
            highlighted = self.highlighted == key or not offset.isNull()
            extents.append((highlighted, layout, map_item, label, geometry, polygon, offset))
        extents.sort(key=lambda extent: extent[0])

        for highlighted, layout, map_item, label, geometry, polygon, offset in extents:
            painter.setPen(QPen(LINE_COLOR, 3 if highlighted else 2))
            painter.setBrush(QBrush(HIGHLIGHT_FILL_COLOR if highlighted else FILL_COLOR))
            painter.drawPolygon(polygon)

            # move handle: white disc with a cross in the center of the extent
            if self.hasHandle(layout, map_item, polygon):
                center = self.handlePosition(geometry) + offset
                painter.setPen(QPen(LINE_COLOR, 2))
                painter.setBrush(QBrush(QColor(255, 255, 255, 230)))
                painter.drawEllipse(center, HANDLE_RADIUS, HANDLE_RADIUS)
                arm = HANDLE_RADIUS - 3
                painter.drawLine(center + QPointF(-arm, 0), center + QPointF(arm, 0))
                painter.drawLine(center + QPointF(0, -arm), center + QPointF(0, arm))

        # labels: inside the top-left corner when they fit, above the extent when it is
        # highlighted, otherwise hidden; never on top of another label
        drawn = []
        for highlighted, layout, map_item, label, geometry, polygon, offset in reversed(extents):
            rect = polygon.boundingRect()
            text_rect = QRectF(metrics.boundingRect(label))
            if text_rect.width() + 12 <= rect.width() and text_rect.height() + 12 <= rect.height():
                baseline = rect.topLeft() + QPointF(6, 6 + metrics.ascent())
            elif highlighted:
                baseline = rect.topLeft() + QPointF(0, -6 - metrics.descent())
            else:
                continue
            label_rect = text_rect.translated(baseline).adjusted(-3, -3, 3, 3)
            if any(label_rect.intersects(other) for other in drawn):
                continue
            drawn.append(label_rect)

            path = QPainterPath()
            path.addText(baseline, font, label)
            painter.setPen(QPen(QColor(255, 255, 255, 220), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                                Qt.PenJoinStyle.RoundJoin))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
            painter.fillPath(path, QBrush(LINE_COLOR.darker(150)))


def movable(layout, map_item):
    """Maps controlled by the atlas get their extent from the atlas feature and cannot be moved"""
    return not (map_item.atlasDriven() and layout.atlas().enabled())


def moveMapExtent(layout, map_item, center, center_crs):
    """Center the map item's extent on a point given in center_crs, as an undoable layout command"""
    if map_item.crs().isValid() and center_crs.isValid() and map_item.crs() != center_crs:
        center = QgsCoordinateTransform(center_crs, map_item.crs(), QgsProject.instance()).transform(center)
    extent = map_item.extent()
    new_extent = QgsRectangle.fromCenterAndSize(center, extent.width(), extent.height())
    layout.undoStack().beginCommand(map_item, 'Move Map Extent')
    map_item.setExtent(new_extent)
    layout.undoStack().endCommand()


class LayoutExtentsMapTool(QgsMapToolPan):
    """Map tool showing the layout map extents: drag to pan, click an extent to open its layout,
    drag the handle in the center of an extent to move it"""

    def __init__(self, map_extents):
        super().__init__(map_extents.canvas)
        self.map_extents = map_extents
        self.press_position = None
        # (layout name, map uuid, start center in canvas CRS) while an extent is being moved
        self.moving = None

    def layoutAt(self, event):
        item = self.map_extents.item
        return item.layoutAt(self.toMapCoordinates(event.pos())) if item else None

    def canvasPressEvent(self, event):
        self.press_position = event.pos()
        item = self.map_extents.item
        handle = item.handleAt(event.pos()) if item and event.button() == Qt.MouseButton.LeftButton else None
        if handle:
            layout, map_item, center = handle
            self.moving = (layout.name(), map_item.uuid(), center)
            item.dragged = (layout.name(), map_item.uuid())
            item.drag_offset = QPointF()
            self.canvas().setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            return
        super().canvasPressEvent(event)

    def canvasMoveEvent(self, event):
        item = self.map_extents.item
        if self.moving and item:
            item.drag_offset = QPointF(event.pos() - self.press_position)
            item.update()
            return
        super().canvasMoveEvent(event)
        if event.buttons() != Qt.MouseButton.NoButton or item is None:
            return
        handle = item.handleAt(event.pos())
        if handle:
            hit = handle[:2]
            self.canvas().setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        else:
            hit = item.extentAt(self.toMapCoordinates(event.pos()))
            self.canvas().setCursor(QCursor(Qt.CursorShape.PointingHandCursor if hit else Qt.CursorShape.OpenHandCursor))
        self.map_extents.setHighlighted((hit[0].name(), hit[1].uuid()) if hit else None)

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton and not self.moving:
            # right-click leaves the tool, like the other QGIS map tools
            self.press_position = None
            self.map_extents.exitTool()
            return
        clicked = (event.button() == Qt.MouseButton.LeftButton and self.press_position is not None
                   and (event.pos() - self.press_position).manhattanLength() <= CLICK_TOLERANCE)
        press_position = self.press_position
        self.press_position = None

        if self.moving:
            self.finishMove(event, press_position, clicked)
            return

        layout = self.layoutAt(event) if clicked else None
        if layout is not None:
            # a plain click on the pan tool recenters the map: skip it when opening a layout
            self.map_extents.panel.iface.openLayoutDesigner(layout)
        else:
            super().canvasReleaseEvent(event)

    def finishMove(self, event, press_position, clicked):
        """Apply the move of an extent dragged by its handle; a click on the handle opens the layout"""
        layout_name, map_uuid, start_center = self.moving
        self.moving = None
        item = self.map_extents.item
        if item:
            item.dragged = None
            item.drag_offset = QPointF()

        # look the map up again: it may have been deleted during the drag
        layout = QgsProject.instance().layoutManager().layoutByName(layout_name)
        map_item = layout.itemByUuid(map_uuid) if layout else None
        if map_item is not None and clicked:
            self.map_extents.panel.iface.openLayoutDesigner(layout)
        elif map_item is not None:
            start = self.toMapCoordinates(press_position)
            end = self.toMapCoordinates(event.pos())
            center = QgsPointXY(start_center.x() + end.x() - start.x(), start_center.y() + end.y() - start.y())
            moveMapExtent(layout, map_item, center, self.canvas().mapSettings().destinationCrs())
        if item:
            item.update()

    def canvasDoubleClickEvent(self, event):
        # the pan tool zooms on double-click; a double-click on an extent already opened the layout
        if self.layoutAt(event) is None:
            super().canvasDoubleClickEvent(event)

    def activate(self):
        super().activate()
        self.map_extents.show()

    def deactivate(self):
        self.map_extents.hide()
        super().deactivate()


class MapExtents(QObject):
    """Map tool showing the extents of all layout maps on the canvas.
    Clicking an extent opens its layout, dragging its center handle moves it."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.panel = parent
        self.canvas = parent.iface.mapCanvas()
        self.item = None
        self.previous_tool = None
        self.relay = SignalRelay(self.refresh, self)

        layout_manager = QgsProject.instance().layoutManager()
        self.relay.watch(layout_manager.layoutAdded)
        self.relay.watch(layout_manager.layoutRemoved)
        self.relay.watch(layout_manager.layoutRenamed)
        self.relay.watch(self.canvas.destinationCrsChanged)

        self.action = QAction(icon('mActionShowLayoutExtents.svg'),
                              'Show Layout Map Extents (click an extent to open its layout, drag its center to move it, right-click to exit)', self)
        self.action.setCheckable(True)
        self.action.triggered.connect(self.activateTool)
        self.map_tool = LayoutExtentsMapTool(self)
        self.map_tool.setAction(self.action)
        parent.tbShowExtents.setDefaultAction(self.action)

    def activateTool(self):
        if self.canvas.mapTool() is not self.map_tool:
            self.previous_tool = self.canvas.mapTool()
        self.canvas.setMapTool(self.map_tool)

    def exitTool(self):
        """Go back to the map tool used before, or to the pan tool"""
        previous_tool, self.previous_tool = self.previous_tool, None
        if previous_tool is not None and not sip.isdeleted(previous_tool):
            self.canvas.setMapTool(previous_tool)
        else:
            self.panel.iface.actionPan().trigger()

    def show(self):
        if self.item is None:
            self.item = MapExtentsItem(self.canvas)
        self.refresh()

    def hide(self):
        if self.item is not None:
            self.canvas.scene().removeItem(self.item)
            self.item = None

    def setHighlighted(self, extent_key):
        """Highlight one extent, given as (layout name, map uuid), or none"""
        if self.item is not None and self.item.highlighted != extent_key:
            self.item.highlighted = extent_key
            self.item.update()

    def refresh(self):
        """Watch layouts and map items so the overlay follows their changes, then repaint"""
        if self.item is None:
            return
        for layout in QgsProject.instance().layoutManager().printLayouts():
            self.relay.watch(layout.changed)
            for item in layout.items():
                if isinstance(item, QgsLayoutItemMap):
                    self.relay.watch(item.extentChanged)
                    self.relay.watch(item.mapRotationChanged)
                    self.relay.watch(item.crsChanged)
        self.item.update()

    def cleanup(self):
        """Remove the map tool and overlay, and disconnect signals when the plugin is unloaded"""
        self.relay.delete()
        if self.canvas.mapTool() is self.map_tool:
            self.canvas.unsetMapTool(self.map_tool)
        self.hide()
