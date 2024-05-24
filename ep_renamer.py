# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import os.path
import re
from xml.dom import minidom
from xml.dom.minidom import Element
from zipfile import ZipFile

MIMETYPE_OPF = "application/oebps-package+xml"


def node_text(node: Element) -> str:
    text = ""

    node.normalize()
    if node.firstChild and node.firstChild.data:
        text = node.firstChild.data.strip()

    return text


class OpfMetadata(object):
    def __init__(self):
        self.titles = []
        self.creators = []
        self.subjects = []
        self.description = None
        self.publisher = None
        self.contributors = []
        self.dates = []
        self.dc_type = None
        self.format = None
        self.identifiers = []
        self.source = None
        self.languages = []
        self.relation = None
        self.coverage = None
        self.right = None
        self.metas = []

    def add_title(self, title, lang=None):
        self.titles.append(title)

    def add_creator(self, name, role=None, file_as=None):
        self.creators.append(name)

    def add_subject(self, subject: str):
        if subject:
            self.subjects.append(subject)

    def add_contributor(self, name, role=None, file_as=None):
        if not name:
            return
        self.contributors.append(name)

    def add_date(self, date, event=None):
        if not date:
            return
        self.dates.append(date)

    def add_identifier(self, content, identifier=None, scheme=None):
        if not content:
            return
        identifier = identifier or ""
        scheme = scheme or ""
        self.identifiers.append((content, identifier, scheme))

    def add_language(self, lang):
        self.languages.append(lang)

    def get_isbn(self):
        l = [x[0] for x in self.identifiers if x[2].lower() == "isbn"]
        isbn = None
        if l:
            isbn = l[0]
        return isbn


def parse_opf(xml_string: bytes) -> OpfMetadata:
    package = minidom.parseString(xml_string).documentElement

    data = {"metadata": None, "manifest": None, "spine": None, "guide": None}
    elements = [e for e in package.childNodes if e.nodeType == e.ELEMENT_NODE]
    for node in elements:
        tag = node.tagName.lower()
        if tag.startswith("opf:"):
            tag = tag[4:].lower()
        data[tag] = node

    return _parse_xml_metadata(data["metadata"])


def _parse_xml_metadata(element: Element) -> OpfMetadata:
    metadata = OpfMetadata()

    for node in element.getElementsByTagName("dc:title"):
        metadata.add_title(node_text(node), node.getAttribute("xml:lang"))

    for node in element.getElementsByTagName("dc:creator"):
        metadata.add_creator(
            node_text(node),
            node.getAttribute("opf:role"),
            node.getAttribute("opf:file-as"),
        )

    for node in element.getElementsByTagName("dc:subject"):
        metadata.add_subject(node_text(node))

    for node in element.getElementsByTagName("dc:description"):
        metadata.description = node_text(node)

    for node in element.getElementsByTagName("dc:publisher"):
        metadata.publisher = node_text(node)

    for node in element.getElementsByTagName("dc:contributor"):
        metadata.add_contributor(
            node_text(node),
            node.getAttribute("opf:role"),
            node.getAttribute("opf:file-as"),
        )

    for node in element.getElementsByTagName("dc:date"):
        metadata.add_date(node_text(node), node.getAttribute("opf:event"))

    for node in element.getElementsByTagName("dc:type"):
        metadata.dc_type = node_text(node)

    for node in element.getElementsByTagName("dc:format"):
        metadata.format = node_text(node)

    for node in element.getElementsByTagName("dc:identifier"):
        metadata.add_identifier(
            node_text(node),
            node.getAttribute("id"),
            node.getAttribute("opf:scheme"),
        )

    for node in element.getElementsByTagName("dc:source"):
        metadata.source = node_text(node)

    for node in element.getElementsByTagName("dc:language"):
        metadata.add_language(node_text(node))

    return metadata


def get_epub_metadata(fname: str) -> OpfMetadata:
    with ZipFile(fname, "r") as fp:
        xmlstring = fp.read("META-INF/container.xml")
        container_xml = minidom.parseString(xmlstring).documentElement
        opf_path = None
        for element in container_xml.getElementsByTagName("rootfile"):
            if element.getAttribute("media-type") == MIMETYPE_OPF:
                # Only take the first full-path available
                opf_path = element.getAttribute("full-path")
                break

        # Read OPF xml file
        xml_string = fp.read(opf_path)
        return parse_opf(xml_string)


def clean_fname(name: str) -> str:
    s = re.sub(r"\s+", " ", str(name)).strip()
    return re.sub(r"(?u)[^-\w.\s]", "", s)


def sanitize_title(s: str) -> str:
    stopwords = ["the", "a", "at"]
    words = [w for w in s.split() if w.lower() not in stopwords]
    return " ".join(words)


def process_file(fname: str, dirpath: str):
    meta = get_epub_metadata(os.path.join(dirpath, fname))
    title = meta.titles[0]
    author = meta.creators[0]
    # print(json.dumps(meta, indent=2))
    destname = clean_fname(f"{title} - {author}")
    if len(destname) > 254:
        destname = destname[:254]
    destname += ".epub"
    if not os.path.exists(os.path.join(dirpath, destname)):
        os.rename(os.path.join(dirpath, fname), os.path.join(dirpath, destname))
        print(f'"{fname}" ==> "{destname}"')


if __name__ == "__main__":
    for dirpath, dnames, fnames in os.walk("./"):
        for f in [f for f in fnames if f.lower().endswith(".epub")]:
            try:
                print(f)
                process_file(f, dirpath)
            except Exception:
                pass
