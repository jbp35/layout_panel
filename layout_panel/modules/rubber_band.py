from qgis.PyQt.QtGui import QColor
from qgis.gui import QgsRubberBand
from qgis.core import QgsWkbTypes, QgsGeometry

class RubberBand():
    def __init__(self,parent=None):
        """Initialize the rubber band"""
        self.parent = parent
        
        self.rubber_band = QgsRubberBand(self.parent.iface.mapCanvas(),QgsWkbTypes.PolygonGeometry)
        color = QColor('#3388ff')
        color.setAlpha(120)
        self.rubber_band.setColor(color)
        self.rubber_band.setWidth(2)

    def drawExtent(self):
        """Show the extent of the selected layout's reference map on the canvas"""
        selected_items = self.parent.listWidget.selectedItems()
        if not selected_items:
            return
        layout = self.parent.layout_item.layoutByName(selected_items[0].text())
        reference_map = layout.referenceMap() if layout else None
        if reference_map is None:
            self.parent.iface.messageBar().pushWarning('Show layout extent', f' "{selected_items[0].text()}" has no map')
            return
        # The polygon is in the map item's CRS; the rubber band reprojects it to the canvas CRS
        geom = QgsGeometry.fromQPolygonF(reference_map.visibleExtentPolygon())
        self.rubber_band.setToGeometry(geom, reference_map.crs())

    def clear(self):
        """Hide the extent"""
        self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)

    def cleanup(self):
        """Remove the rubber band from the canvas when the plugin is unloaded"""
        self.clear()
        self.parent.iface.mapCanvas().scene().removeItem(self.rubber_band)
