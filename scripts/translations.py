"""Update and compile the plugin translations, with Python only (no Qt tools needed).

    python scripts/translations.py update   # add new texts of the code to the .ts files
    python scripts/translations.py compile  # compile the .ts files to the .qm files QGIS loads

Texts are the string literals passed to tr() or trNoop() in the Python files
(see layout_panel/modules/i18n.py) and the translatable strings of the .ui
files. Translate the .ts files with Qt Linguist or a text editor, then
compile them and commit both the .ts and the .qm files: the .qm files are
shipped in the plugin package.
"""

import ast
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / 'layout_panel'
I18N_DIR = PLUGIN_DIR / 'i18n'
LANGUAGES = ['fr', 'es', 'de']
CONTEXT = 'LayoutPanel'


def extract():
    """Return {context: [source texts]} found in the plugin, in order of appearance"""
    texts = {}

    def add(context, text):
        if text and text not in texts.setdefault(context, []):
            texts[context].append(text)

    for path in sorted(PLUGIN_DIR.rglob('*.py')):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id in ('tr', 'trNoop') and node.args
                    and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                add(CONTEXT, node.args[0].value)

    for path in sorted(PLUGIN_DIR.rglob('*.ui')):
        ui = ET.parse(path).getroot()
        # uic translates the texts of a .ui file in the context of its top level class
        context = ui.findtext('class')
        for string in ui.iter('string'):
            if string.get('notr') != 'true':
                add(context, string.text)
    return texts


def update():
    """Add the texts of the code to the .ts files, keeping existing translations"""
    I18N_DIR.mkdir(exist_ok=True)
    texts = extract()
    for language in LANGUAGES:
        path = I18N_DIR / f'layout_panel_{language}.ts'
        translations = readTs(path) if path.exists() else {}
        root = ET.Element('TS', version='2.1', language=language)
        for context, sources in texts.items():
            context_element = ET.SubElement(root, 'context')
            ET.SubElement(context_element, 'name').text = context
            for source in sources:
                message = ET.SubElement(context_element, 'message')
                ET.SubElement(message, 'source').text = source
                translation = ET.SubElement(message, 'translation')
                if translations.get((context, source)):
                    translation.text = translations[(context, source)]
                else:
                    translation.set('type', 'unfinished')
        ET.indent(root)
        with open(path, 'w', encoding='utf-8', newline='\n') as file:
            file.write('<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE TS>\n')
            file.write(ET.tostring(root, encoding='unicode'))
            file.write('\n')
        missing = sum(1 for context in texts for source in texts[context] if not translations.get((context, source)))
        print(f'{path.name}: {sum(map(len, texts.values()))} texts, {missing} to translate')


def readTs(path):
    """Return {(context, source): translation} of a .ts file, skipping unfinished and obsolete ones"""
    translations = {}
    for context in ET.parse(path).getroot().iter('context'):
        name = context.findtext('name')
        for message in context.iter('message'):
            translation = message.find('translation')
            if translation is None or translation.get('type') in ('unfinished', 'obsolete', 'vanished'):
                continue
            translations[(name, message.findtext('source'))] = translation.text or ''
    return translations


def elfHash(data):
    """Hash of the source text used by QTranslator to find messages"""
    h = 0
    for byte in data:
        h = ((h << 4) + byte) & 0xFFFFFFFF
        g = h & 0xF0000000
        if g:
            h ^= g >> 24
        h &= ~g & 0xFFFFFFFF
    return h or 1


def writeQm(translations, path):
    """Write translations {(context, source): translation} in the binary .qm format read by QTranslator"""
    messages = bytearray()
    hashes = []
    for (context, source), translation in sorted(translations.items()):
        source_bytes = source.encode('utf-8')
        context_bytes = context.encode('utf-8')
        translation_bytes = translation.encode('utf-16-be')
        hashes.append((elfHash(source_bytes), len(messages)))
        messages += struct.pack('>BI', 0x03, len(translation_bytes)) + translation_bytes  # translation
        messages += struct.pack('>BI', 0x06, len(source_bytes)) + source_bytes  # source text
        messages += struct.pack('>BI', 0x07, len(context_bytes)) + context_bytes  # context
        messages += b'\x01'  # end of message
    hash_table = b''.join(struct.pack('>II', h, offset) for h, offset in sorted(hashes))

    magic = bytes([0x3C, 0xB8, 0x64, 0x18, 0xCA, 0xEF, 0x9C, 0x95, 0xCD, 0x21, 0x1C, 0xBF, 0x60, 0xA1, 0xBD, 0xDD])
    with open(path, 'wb') as file:
        file.write(magic)
        file.write(struct.pack('>BI', 0x42, len(hash_table)) + hash_table)  # hashes
        file.write(struct.pack('>BI', 0x69, len(messages)) + bytes(messages))  # messages


def compile():
    for language in LANGUAGES:
        path = I18N_DIR / f'layout_panel_{language}.ts'
        translations = readTs(path)
        writeQm(translations, path.with_suffix('.qm'))
        print(f'{path.with_suffix(".qm").name}: {len(translations)} translations')


if __name__ == '__main__':
    commands = {'update': update, 'compile': compile}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        sys.exit(__doc__)
    commands[sys.argv[1]]()
