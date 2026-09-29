"""Build the basic layout templates shipped in layout_panel/templates.

Run from the QGIS Python console:

    exec(open('scripts/build_templates.py').read())
    build_all('layout_panel/templates')

Each template is one page (A4 to A0, portrait and landscape) with a map
filling the page inside the margins, the project title, a scale bar and a
north arrow. Maps are saved with a placeholder extent: when a layout is
created from one of these templates, the plugin zooms its map to the map
canvas (see Project.zoomMapsToCanvas). Texts use Open Sans, which QGIS
offers to download when it is missing.
"""
import os

from qgis.core import (
    Qgis, QgsProject, QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel,
    QgsLayoutItemScaleBar, QgsLayoutItemPicture, QgsLayoutSize, QgsLayoutPoint,
    QgsLayoutMeasurement, QgsTextFormat, QgsTextBufferSettings, QgsReadWriteContext,
    QgsRectangle,
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor, QFont

FONT = 'Open Sans'
DARK = QColor(40, 40, 40)
NORTH_ARROW = ':/images/north_arrows/layout_default_north_arrow.svg'
TITLE = "[% coalesce(nullif(@project_title, ''), nullif(@project_basename, ''), 'Map title') %]"

# ISO 216 sizes in mm, short side first
PAPER_SIZES = {
    'A4': (210, 297),
    'A3': (297, 420),
    'A2': (420, 594),
    'A1': (594, 841),
    'A0': (841, 1189),
}


def text_format(size, bold=False):
    fmt = QgsTextFormat()
    font = QFont(FONT)
    font.setBold(bold)
    fmt.setFont(font)
    fmt.setSize(size)
    fmt.setSizeUnit(Qgis.RenderUnit.Points)
    fmt.setColor(DARK)
    # white halo keeps texts readable over the map
    buffer = QgsTextBufferSettings()
    buffer.setEnabled(True)
    buffer.setColor(QColor(255, 255, 255))
    buffer.setSize(size * 0.08)
    buffer.setSizeUnit(Qgis.RenderUnit.Millimeters)
    fmt.setBuffer(buffer)
    return fmt


def build(project, name, width, height):
    # items grow a bit slower than the paper: A4 x1, A3 x1.3, A0 x2.8
    k = (min(width, height) / 210.0) ** 0.75
    margin = 10 * k
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(name)
    layout.pageCollection().page(0).setPageSize(QgsLayoutSize(width, height))

    main = QgsLayoutItemMap(layout)
    main.setId('Main map')
    main.setFrameEnabled(True)
    main.setFrameStrokeColor(QColor(90, 90, 90))
    main.setFrameStrokeWidth(QgsLayoutMeasurement(0.3 * k))
    layout.addLayoutItem(main)
    main.attemptMove(QgsLayoutPoint(margin, margin))
    main.attemptResize(QgsLayoutSize(width - 2 * margin, height - 2 * margin))
    # placeholder extent, the plugin zooms the map to the canvas when a layout is created
    main.zoomToExtent(QgsRectangle(-180, -90, 180, 90))

    inset = 5 * k
    arrow_w, arrow_h = 8 * k, 12 * k
    title = QgsLayoutItemLabel(layout)
    title.setId('Title')
    title.setText(TITLE)
    title.setTextFormat(text_format(18 * k, True))
    title.setHAlign(Qt.AlignmentFlag.AlignLeft)
    title.setVAlign(Qt.AlignmentFlag.AlignTop)
    title.setMarginX(0)
    title.setMarginY(0)
    layout.addLayoutItem(title)
    title.attemptMove(QgsLayoutPoint(margin + inset, margin + inset))
    title.attemptResize(QgsLayoutSize(width - 2 * (margin + inset) - arrow_w - inset, 12 * k))

    arrow = QgsLayoutItemPicture(layout)
    arrow.setId('North arrow')
    arrow.setPicturePath(NORTH_ARROW)
    arrow.setLinkedMap(main)
    arrow.setNorthMode(QgsLayoutItemPicture.NorthMode.GridNorth)
    arrow.setResizeMode(QgsLayoutItemPicture.ResizeMode.Zoom)
    layout.addLayoutItem(arrow)
    arrow.attemptMove(QgsLayoutPoint(width - margin - inset - arrow_w, margin + inset))
    arrow.attemptResize(QgsLayoutSize(arrow_w, arrow_h))

    bar = QgsLayoutItemScaleBar(layout)
    bar.setId('Scale bar')
    bar.setStyle('Single Box')
    bar.setLinkedMap(main)
    bar.setUnits(Qgis.DistanceUnit.Kilometers)
    bar.setUnitLabel('km')
    bar.setNumberOfSegmentsLeft(0)
    bar.setNumberOfSegments(4)
    bar.setSegmentSizeMode(Qgis.ScaleBarSegmentSizeMode.FitWidth)
    bar.setMinimumBarWidth(40 * k)
    bar.setMaximumBarWidth(60 * k)
    bar.setHeight(1.8 * k)
    bar.setTextFormat(text_format(7 * k))
    bar.setLabelBarSpace(1 * k)
    bar.setBoxContentSpace(1.5 * k)
    bar.setBackgroundEnabled(True)
    bar.setBackgroundColor(QColor(255, 255, 255, 220))
    layout.addLayoutItem(bar)
    bar.setReferencePoint(QgsLayoutItemScaleBar.ReferencePoint.LowerLeft)
    bar.attemptMove(QgsLayoutPoint(margin + inset, height - margin - inset))
    return layout


def templates():
    """Template name -> (width, height) for every paper size in both orientations"""
    result = {}
    for paper, (short, long) in PAPER_SIZES.items():
        result[paper + '_Portrait'] = (short, long)
        result[paper + '_Landscape'] = (long, short)
    return result


def build_all(out_dir, project=None):
    project = project or QgsProject()
    paths = []
    for name, (width, height) in templates().items():
        layout = build(project, name, width, height)
        path = os.path.join(out_dir, name + '.qpt')
        paths.append((path, layout.saveAsTemplate(path, QgsReadWriteContext())))
    return paths
