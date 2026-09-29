"""Build the generic layout templates shipped in layout_panel/templates.

Run from the QGIS Python console:

    exec(open('scripts/build_templates.py').read())
    build_all('layout_panel/templates')

Maps are saved with a placeholder extent: when a layout is created from one
of these templates, the plugin zooms its maps to the map canvas (see
Project.zoomMapsToCanvas). Texts use Open Sans, which QGIS offers to download
when it is missing.
"""
from qgis.core import (
    Qgis, QgsProject, QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel,
    QgsLayoutItemLegend, QgsLayoutItemScaleBar, QgsLayoutItemPicture, QgsLayoutItemShape,
    QgsLayoutItemMapOverview, QgsLayoutSize, QgsLayoutPoint, QgsLayoutMeasurement,
    QgsTextFormat, QgsReadWriteContext, QgsFillSymbol,
    QgsLegendStyle, QgsRectangle,
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor, QFont

FONT = 'Open Sans'
ACCENT = QColor(38, 70, 100)
DARK = QColor(40, 40, 40)
GREY = QColor(105, 105, 105)
FRAME = QColor(90, 90, 90)
NORTH_ARROW = ':/images/north_arrows/layout_default_north_arrow.svg'

TITLE = "[% coalesce(nullif(@project_title, ''), 'Map title') %]"
SUBTITLE = 'Subtitle or short description of the map'
DATE = "[% format_date(now(), 'yyyy-MM-dd') %]"
AUTHOR = "[% coalesce(nullif(@user_full_name, ''), @user_account_name) %]"


def crs(map_id):
    return "[% item_variables('" + map_id + "')['map_crs'] %]"


def scale_text(map_id):
    return "Scale 1:[% format_number(item_variables('" + map_id + "')['map_scale'], 0) %]"


def text_format(size, bold=False, color=DARK):
    fmt = QgsTextFormat()
    font = QFont(FONT)
    font.setBold(bold)
    fmt.setFont(font)
    fmt.setSize(size)
    fmt.setSizeUnit(Qgis.RenderUnit.Points)
    fmt.setColor(color)
    return fmt


def place(item, x, y, w, h):
    item.attemptMove(QgsLayoutPoint(x, y))
    item.attemptResize(QgsLayoutSize(w, h))


def new_layout(project, name, width, height):
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(name)
    layout.pageCollection().page(0).setPageSize(QgsLayoutSize(width, height))
    return layout


def add_label(layout, text, x, y, w, h, size, bold=False, color=DARK,
              halign=Qt.AlignmentFlag.AlignLeft, valign=Qt.AlignmentFlag.AlignTop, item_id=None):
    label = QgsLayoutItemLabel(layout)
    label.setText(text)
    label.setTextFormat(text_format(size, bold, color))
    label.setHAlign(halign)
    label.setVAlign(valign)
    label.setMarginX(0)
    label.setMarginY(0)
    layout.addLayoutItem(label)
    place(label, x, y, w, h)
    if item_id:
        label.setId(item_id)
    return label


def add_rect(layout, x, y, w, h, color, item_id=None):
    shape = QgsLayoutItemShape(layout)
    shape.setShapeType(QgsLayoutItemShape.Shape.Rectangle)
    shape.setSymbol(QgsFillSymbol.createSimple({
        'color': color.name(), 'outline_style': 'no'}))
    layout.addLayoutItem(shape)
    place(shape, x, y, w, h)
    if item_id:
        shape.setId(item_id)
    return shape


def add_map(layout, x, y, w, h, item_id):
    map_item = QgsLayoutItemMap(layout)
    map_item.setId(item_id)
    map_item.setFrameEnabled(True)
    map_item.setFrameStrokeColor(FRAME)
    map_item.setFrameStrokeWidth(QgsLayoutMeasurement(0.3))
    layout.addLayoutItem(map_item)
    place(map_item, x, y, w, h)
    # placeholder extent, the plugin zooms maps to the canvas when a layout is created
    map_item.zoomToExtent(QgsRectangle(-180, -90, 180, 90))
    return map_item


def add_overview(layout, main_map, x, y, w, h, item_id='Overview map'):
    overview = add_map(layout, x, y, w, h, item_id)
    frame = QgsLayoutItemMapOverview('Main map extent', overview)
    frame.setLinkedMap(main_map)
    frame.setFrameSymbol(QgsFillSymbol.createSimple({
        'color': '215,48,39,40', 'outline_color': '215,48,39,255', 'outline_width': '0.5'}))
    overview.overviews().addOverview(frame)
    return overview


def add_legend(layout, map_item, x, y, w, h, columns=1, title_size=10, item_size=8):
    legend = QgsLayoutItemLegend(layout)
    legend.setTitle('Legend')
    legend.setLinkedMap(map_item)
    legend.setLegendFilterByMapEnabled(True)
    legend.setAutoUpdateModel(True)
    legend.setResizeToContents(False)
    legend.setColumnCount(columns)
    legend.setSplitLayer(False)
    legend.setEqualColumnWidth(True)
    legend.setBoxSpace(0)
    legend.setWrapString('')
    styles = {
        QgsLegendStyle.Style.Title: text_format(title_size, True),
        QgsLegendStyle.Style.Group: text_format(item_size, True),
        QgsLegendStyle.Style.Subgroup: text_format(item_size, True),
        QgsLegendStyle.Style.SymbolLabel: text_format(item_size),
    }
    for style, fmt in styles.items():
        legend.rstyle(style).setTextFormat(fmt)
    legend.setSymbolWidth(item_size * 0.75)
    legend.setSymbolHeight(item_size * 0.5)
    layout.addLayoutItem(legend)
    place(legend, x, y, w, h)
    legend.setId('Legend')
    return legend


def add_scalebar(layout, map_item, x, y, w, size=7):
    bar = QgsLayoutItemScaleBar(layout)
    bar.setStyle('Single Box')
    bar.setLinkedMap(map_item)
    bar.setUnits(Qgis.DistanceUnit.Kilometers)
    bar.setUnitLabel('km')
    bar.setNumberOfSegmentsLeft(0)
    bar.setNumberOfSegments(4)
    bar.setSegmentSizeMode(Qgis.ScaleBarSegmentSizeMode.FitWidth)
    bar.setMinimumBarWidth(w * 0.55)
    bar.setMaximumBarWidth(w * 0.9)
    bar.setHeight(size * 0.25)
    bar.setTextFormat(text_format(size))
    bar.setLabelBarSpace(1)
    bar.setBoxContentSpace(0)
    layout.addLayoutItem(bar)
    bar.attemptMove(QgsLayoutPoint(x, y))
    bar.setId('Scale bar')
    return bar


def add_north_arrow(layout, map_item, x, y, w, h):
    arrow = QgsLayoutItemPicture(layout)
    arrow.setPicturePath(NORTH_ARROW)
    arrow.setLinkedMap(map_item)
    arrow.setNorthMode(QgsLayoutItemPicture.NorthMode.GridNorth)
    arrow.setResizeMode(QgsLayoutItemPicture.ResizeMode.Zoom)
    layout.addLayoutItem(arrow)
    place(arrow, x, y, w, h)
    arrow.setId('North arrow')
    return arrow


def portrait(project, name, width, height):
    """Title on top, large map, legend and scale at the bottom."""
    k = width / 210.0
    m = 10 * k
    inner = width - 2 * m
    layout = new_layout(project, name, width, height)
    add_rect(layout, m, m, inner, 1.2 * k, ACCENT, 'Accent bar')
    add_label(layout, TITLE, m, m + 4 * k, inner, 11 * k, 20 * k, True, item_id='Title')
    add_label(layout, SUBTITLE, m, m + 16 * k, inner, 7 * k, 11 * k, color=GREY, item_id='Subtitle')

    map_top = m + 25 * k
    footer_top = height - m - 6 * k
    bottom_top = footer_top - 48 * k
    main = add_map(layout, m, map_top, inner, bottom_top - 4 * k - map_top, 'Main map')
    add_north_arrow(layout, main, width - m - 12 * k, map_top + 4 * k, 8 * k, 12 * k)

    add_legend(layout, main, m, bottom_top, inner * 0.62, 44 * k, columns=2,
               title_size=10 * k, item_size=8 * k)
    right = m + inner * 0.66
    add_scalebar(layout, main, right, bottom_top + 2 * k, inner * 0.34, 7 * k)
    add_label(layout, scale_text('Main map'), right, bottom_top + 14 * k, inner * 0.34, 5 * k, 8 * k,
              color=GREY, item_id='Scale')

    add_rect(layout, m, footer_top, inner, 0.3 * k, GREY, 'Footer line')
    footer = ('Author: %s   |   Date: %s   |   CRS: %s   |   Sources: to be completed'
              % (AUTHOR, DATE, crs('Main map')))
    add_label(layout, footer, m, footer_top + 1.5 * k, inner, 4.5 * k, 7 * k, color=GREY, item_id='Footer')
    return layout


def landscape(project, name, width, height):
    """Large map on the left, title, overview, legend and scale in a side panel."""
    k = width / 297.0
    m = 10 * k
    side_w = 65 * k
    gap = 5 * k
    side_x = width - m - side_w
    layout = new_layout(project, name, width, height)
    main = add_map(layout, m, m, side_x - gap - m, height - 2 * m, 'Main map')

    y = m
    add_rect(layout, side_x, y, side_w, 1.2 * k, ACCENT, 'Accent bar')
    add_label(layout, TITLE, side_x, y + 4 * k, side_w, 18 * k, 16 * k, True, item_id='Title')
    add_label(layout, SUBTITLE, side_x, y + 23 * k, side_w, 10 * k, 9 * k, color=GREY, item_id='Subtitle')
    add_overview(layout, main, side_x, y + 36 * k, side_w, 45 * k)
    add_legend(layout, main, side_x, y + 86 * k, side_w, 66 * k, title_size=10 * k, item_size=8 * k)

    bottom = height - m
    add_north_arrow(layout, main, side_x, bottom - 42 * k, 8 * k, 12 * k)
    add_scalebar(layout, main, side_x + 12 * k, bottom - 40 * k, side_w - 12 * k, 7 * k)
    add_label(layout, scale_text('Main map'), side_x + 12 * k, bottom - 33 * k, side_w - 12 * k, 4 * k,
              7 * k, color=GREY, item_id='Scale')

    add_rect(layout, side_x, bottom - 25 * k, side_w, 0.3 * k, GREY, 'Footer line')
    footer = ('Author: %s\nDate: %s\nCRS: %s\nSources: to be completed'
              % (AUTHOR, DATE, crs('Main map')))
    add_label(layout, footer, side_x, bottom - 23 * k, side_w, 23 * k, 7 * k, color=GREY, item_id='Footer')
    return layout


def comparison(project, name, width, height):
    """Two maps side by side, e.g. before/after or two map themes of the same area."""
    m = 10
    inner = width - 2 * m
    gap = 5
    layout = new_layout(project, name, width, height)
    add_rect(layout, m, m, inner, 1.2, ACCENT, 'Accent bar')
    add_label(layout, TITLE, m, m + 3.5, inner, 9, 18, True, item_id='Title')
    add_label(layout, SUBTITLE, m, m + 13, inner, 6, 10, color=GREY, item_id='Subtitle')

    top = m + 22
    footer_top = height - m - 5
    bottom_top = footer_top - 36
    map_w = (inner - gap) / 2
    map_h = bottom_top - 3 - top - 7
    maps = []
    for i, caption in enumerate(('Map A', 'Map B')):
        x = m + i * (map_w + gap)
        add_label(layout, caption, x, top, map_w, 6, 11, True, color=ACCENT, item_id=caption + ' caption')
        maps.append(add_map(layout, x, top + 7, map_w, map_h, caption))

    add_north_arrow(layout, maps[1], width - m - 11, top + 11, 7, 10.5)
    add_legend(layout, maps[0], m, bottom_top, inner * 0.66, 34, columns=3, title_size=9, item_size=7.5)
    right = m + inner * 0.70
    add_scalebar(layout, maps[0], right, bottom_top + 1, inner * 0.30, 7)
    add_label(layout, scale_text('Map A'), right, bottom_top + 13, inner * 0.30, 4, 7, color=GREY, item_id='Scale')

    add_rect(layout, m, footer_top, inner, 0.3, GREY, 'Footer line')
    footer = ('Author: %s   |   Date: %s   |   CRS: %s   |   Sources: to be completed'
              % (AUTHOR, DATE, crs('Map A')))
    add_label(layout, footer, m, footer_top + 1.3, inner, 4, 7, color=GREY, item_id='Footer')
    return layout


TEMPLATES = {
    'A4_Portrait': (portrait, 210, 297),
    'A3_Portrait': (portrait, 297, 420),
    'A4_Landscape': (landscape, 297, 210),
    'A3_Landscape': (landscape, 420, 297),
    'A4_Landscape_Comparison': (comparison, 297, 210),
}


def build_all(out_dir, project=None):
    import os
    project = project or QgsProject()
    paths = []
    for name, (builder, width, height) in TEMPLATES.items():
        layout = builder(project, name, width, height)
        path = os.path.join(out_dir, name + '.qpt')
        ok = layout.saveAsTemplate(path, QgsReadWriteContext())
        paths.append((path, ok))
    return paths
