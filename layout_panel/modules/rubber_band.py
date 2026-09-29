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
        layout_manager=self.parent.project.getLayoutManager()
        layout = layout_manager.layoutByName(self.parent.listWidget.selectedItems()[0].text())
        reference_map=layout.referenceMap()
        extent=reference_map.visibleExtentPolygon()
        geom = QgsGeometry.fromQPolygonF(extent)
        self.rubber_band.setToGeometry(geom)
