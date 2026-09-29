from qgis.PyQt.QtCore import QEvent, QObject, QPointF, QRectF, Qt
from qgis.PyQt.QtGui import QBrush, QColor, QFont, QPainterPath, QPen, QPolygonF
from qgis.core import (QgsCoordinateTransform, QgsCsException, QgsGeometry, QgsLayoutItemMap,
                       QgsPointXY, QgsProject, QgsSettings)
from qgis.gui import QgsMapCanvasItem

from .signal_relay import SignalRelay

SETTINGS_KEY = 'layout_panel/showMapExtents'
LINE_COLOR = QColor('#3388ff')
FILL_COLOR = QColor(51, 136, 255, 40)


class MapExtentsItem(QgsMapCanvasItem):
    """Canvas item drawing the extent of every map item of every print layout,
    labelled with the layout name"""

    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
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

        for _, label, geometry in self.extents():
            polygon = QPolygonF([self.toCanvasCoordinates(QgsPointXY(vertex.x(), vertex.y()))
                                 for vertex in geometry.vertices()])
            painter.setPen(QPen(LINE_COLOR, 2))
            painter.setBrush(QBrush(FILL_COLOR))
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


class MapExtents(QObject):
    """Toggle the display of layout map extents on the map canvas.
    Double-clicking an extent opens its layout."""

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

        button = parent.tbShowExtents
        button.setChecked(QgsSettings().value(SETTINGS_KEY, False, type=bool))
        button.toggled.connect(self.setVisible)
        self.setVisible(button.isChecked())

    def setVisible(self, visible):
        QgsSettings().setValue(SETTINGS_KEY, visible)
        if visible and self.item is None:
            self.item = MapExtentsItem(self.canvas)
            self.canvas.viewport().installEventFilter(self)
        elif not visible and self.item is not None:
            self.removeItem()
        self.refresh()

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

    def removeItem(self):
        self.canvas.viewport().removeEventFilter(self)
        self.canvas.scene().removeItem(self.item)
        self.item = None

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.MouseButtonDblClick and self.item is not None:
            map_point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
            layout = self.item.layoutAt(map_point)
            if layout is not None:
                self.panel.iface.openLayoutDesigner(layout)
                return True
        return False

    def cleanup(self):
        """Remove the overlay and disconnect signals when the plugin is unloaded"""
        self.relay.delete()
        if self.item is not None:
            self.removeItem()
