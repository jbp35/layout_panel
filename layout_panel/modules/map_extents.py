from qgis.PyQt.QtCore import QObject, QPointF, QRectF, Qt
from qgis.PyQt.QtGui import QAction, QBrush, QColor, QCursor, QFont, QPainterPath, QPen, QPolygonF
from qgis.core import (QgsApplication, QgsCoordinateTransform, QgsCsException, QgsGeometry, QgsLayoutItemMap,
                       QgsPointXY, QgsProject)
from qgis.gui import QgsMapCanvasItem, QgsMapToolPan

from .signal_relay import SignalRelay

LINE_COLOR = QColor('#3388ff')
FILL_COLOR = QColor(51, 136, 255, 40)
HIGHLIGHT_FILL_COLOR = QColor(51, 136, 255, 110)
# a press and release closer than this (in pixels) is a click, not a pan
CLICK_TOLERANCE = 4


class MapExtentsItem(QgsMapCanvasItem):
    """Canvas item drawing the extent of every map item of every print layout,
    labelled with the layout name"""

    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        # name of the layout under the cursor (names, not layouts: QGIS may delete them)
        self.highlighted = None
        self.setZValue(1000)

    def extents(self):
        """Return (layout, label, polygon in canvas CRS) for each layout map"""
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
                extents.append((layout, label, geometry))
        return extents

    def layoutAt(self, map_point):
        """Return the layout whose map extent contains the point, preferring the smallest extent"""
        point = QgsGeometry.fromPointXY(map_point)
        hits = [(geometry.area(), layout) for layout, _, geometry in self.extents() if geometry.contains(point)]
        return min(hits, key=lambda hit: hit[0])[1] if hits else None

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

        for layout, label, geometry in self.extents():
            polygon = QPolygonF([self.toCanvasCoordinates(QgsPointXY(vertex.x(), vertex.y()))
                                 for vertex in geometry.vertices()])
            highlighted = layout.name() == self.highlighted
            painter.setPen(QPen(LINE_COLOR, 3 if highlighted else 2))
            painter.setBrush(QBrush(HIGHLIGHT_FILL_COLOR if highlighted else FILL_COLOR))
            painter.drawPolygon(polygon)

            # label inside the top-left corner, with a white halo for readability
            corner = polygon.boundingRect().topLeft() + QPointF(6, 6 + painter.fontMetrics().ascent())
            path = QPainterPath()
            path.addText(corner, font, label)
            painter.setPen(QPen(QColor(255, 255, 255, 220), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                                Qt.PenJoinStyle.RoundJoin))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
            painter.fillPath(path, QBrush(LINE_COLOR.darker(150)))


class LayoutExtentsMapTool(QgsMapToolPan):
    """Map tool showing the layout map extents: drag to pan, click an extent to open its layout"""

    def __init__(self, map_extents):
        super().__init__(map_extents.canvas)
        self.map_extents = map_extents
        self.press_position = None

    def layoutAt(self, event):
        item = self.map_extents.item
        return item.layoutAt(self.toMapCoordinates(event.pos())) if item else None

    def canvasPressEvent(self, event):
        self.press_position = event.pos()
        super().canvasPressEvent(event)

    def canvasMoveEvent(self, event):
        super().canvasMoveEvent(event)
        if event.buttons() != Qt.MouseButton.NoButton:
            return
        layout = self.layoutAt(event)
        self.map_extents.setHighlighted(layout.name() if layout else None)
        self.canvas().setCursor(QCursor(Qt.CursorShape.PointingHandCursor if layout else Qt.CursorShape.OpenHandCursor))

    def canvasReleaseEvent(self, event):
        clicked = (event.button() == Qt.MouseButton.LeftButton and self.press_position is not None
                   and (event.pos() - self.press_position).manhattanLength() <= CLICK_TOLERANCE)
        self.press_position = None
        layout = self.layoutAt(event) if clicked else None
        if layout is not None:
            # a plain click on the pan tool recenters the map: skip it when opening a layout
            self.map_extents.panel.iface.openLayoutDesigner(layout)
        else:
            super().canvasReleaseEvent(event)

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
    Clicking an extent opens its layout."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.panel = parent
        self.canvas = parent.iface.mapCanvas()
        self.item = None
        self.relay = SignalRelay(self.refresh, self)

        layout_manager = QgsProject.instance().layoutManager()
        self.relay.watch(layout_manager.layoutAdded)
        self.relay.watch(layout_manager.layoutRemoved)
        self.relay.watch(layout_manager.layoutRenamed)
        self.relay.watch(self.canvas.destinationCrsChanged)

        self.action = QAction(QgsApplication.getThemeIcon('/mLayoutItemMap.svg'),
                              'Show Layout Map Extents (click an extent to open its layout)', self)
        self.action.setCheckable(True)
        self.action.triggered.connect(self.activateTool)
        self.map_tool = LayoutExtentsMapTool(self)
        self.map_tool.setAction(self.action)
        parent.tbShowExtents.setDefaultAction(self.action)

    def activateTool(self):
        self.canvas.setMapTool(self.map_tool)

    def show(self):
        if self.item is None:
            self.item = MapExtentsItem(self.canvas)
        self.refresh()

    def hide(self):
        if self.item is not None:
            self.canvas.scene().removeItem(self.item)
            self.item = None

    def setHighlighted(self, layout_name):
        if self.item is not None and self.item.highlighted != layout_name:
            self.item.highlighted = layout_name
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
