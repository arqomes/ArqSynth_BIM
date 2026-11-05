"""An HTML page printed to PDF (0.167: the calculation report) by Qt's own text engine — A4 portrait; Qt breaks it
into pages with its 2 cm margins and numbers them. No browser, no library added. (0.233) Its drawings (inline SVG,
which the text engine does not draw) made pictures first, at their paper size."""

import re

from PySide6 import QtCore, QtGui, QtSvg

SVG = re.compile(r"<svg\b.*?</svg>", re.S)
SIZE = re.compile(r'width="([\d.]+)mm" height="([\d.]+)mm"')
DPI = 200                       # (0.233) a drawing's picture this fine
PAGE_PX = 640                   # …at most this wide in the page (A4 less its margins, at the engine's 96 dpi)


def html_to_pdf(page, path):
    writer = QtGui.QPdfWriter(path)
    writer.setPageSize(QtGui.QPageSize(QtGui.QPageSize.PageSizeId.A4))
    writer.setPageMargins(QtCore.QMarginsF(0, 0, 0, 0), QtGui.QPageLayout.Unit.Millimeter)
    writer.setTitle("ArqSynth BIM")
    document = QtGui.QTextDocument()
    document.setDefaultFont(QtGui.QFont("Arial", 9))
    document.setHtml(_with_pictures(page, document))
    document.print_(writer)
    return path


def _with_pictures(page, document):
    """(0.233) The page with each inline SVG replaced by a picture of it, kept as the document's resource."""
    count = [0]

    def picture(match):
        text = match.group(0)
        size = SIZE.search(text)
        renderer = QtSvg.QSvgRenderer(QtCore.QByteArray(text.encode("utf-8")))
        if size is None or not renderer.isValid():
            return ""
        w_mm, h_mm = float(size.group(1)), float(size.group(2))
        image = QtGui.QImage(max(int(w_mm / 25.4 * DPI), 1), max(int(h_mm / 25.4 * DPI), 1),
                             QtGui.QImage.Format.Format_RGB32)
        image.fill(QtGui.QColor("white"))
        painter = QtGui.QPainter(image)
        renderer.render(painter)
        painter.end()
        name = "arq-drawing-{}".format(count[0])
        count[0] += 1
        document.addResource(QtGui.QTextDocument.ResourceType.ImageResource, QtCore.QUrl(name), image)
        width = min(w_mm / 25.4 * 96, PAGE_PX)
        return '<img src="{}" width="{:.0f}" height="{:.0f}">{}'.format(name, width, width * h_mm / w_mm,
                                                                        "&nbsp;" * 6)      # (0.234: one beside)

    return SVG.sub(picture, page)
