#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import argparse
from typing import List, Optional
from dataclasses import dataclass, field
import xml.etree.ElementTree as ET

@dataclass
class FileNode:
    name: str

@dataclass
class DirectoryNode:
    name: str
    files: List[FileNode] = field(default_factory=list)
    subdirectories: List['DirectoryNode'] = field(default_factory=list)

def list_files(
    startpath: str, 
    show_hidden: bool = False, 
    level: int = 0, 
    max_depth: Optional[int] = None
) -> DirectoryNode:
    if max_depth is not None and level > max_depth:
        return None

    name = os.path.basename(startpath) if level > 0 else startpath
    directory_node = DirectoryNode(name=name)

    try:
        for entry in os.scandir(startpath):
            if not show_hidden and entry.name.startswith('.'):
                continue
            if entry.is_file():
                directory_node.files.append(FileNode(name=entry.name))
            elif entry.is_dir():
                subdirectory_node = list_files(entry.path, show_hidden, level + 1, max_depth)
                if subdirectory_node:
                    directory_node.subdirectories.append(subdirectory_node)
    except PermissionError:
        pass  # Skip directories for which we don't have permission

    return directory_node

def print_directory(node: DirectoryNode, indent: str = '') -> None:
    print(f"{indent}{node.name}")
    sub_indent = indent + '  '
    for file in node.files:
        print(f"{sub_indent}{file.name}")
    for subdirectory in node.subdirectories:
        print_directory(subdirectory, sub_indent)

def save_to_xml(directory_node: DirectoryNode, filepath: str) -> None:
    def to_element(node: DirectoryNode) -> ET.Element:
        element = ET.Element('directory', name=node.name)
        for file_node in node.files:
            file_element = ET.SubElement(element, 'file', name=file_node.name)
        for sub_node in node.subdirectories:
            element.append(to_element(sub_node))
        return element

    root = to_element(directory_node)
    tree = ET.ElementTree(root)
    tree.write(filepath, encoding='utf-8', xml_declaration=True)

def load_from_xml(filepath: str) -> DirectoryNode:
    def from_element(element: ET.Element) -> DirectoryNode:
        directory_node = DirectoryNode(name=element.attrib['name'])
        for child in element:
            if child.tag == 'file':
                directory_node.files.append(FileNode(name=child.attrib['name']))
            elif child.tag == 'directory':
                directory_node.subdirectories.append(from_element(child))
        return directory_node

    tree = ET.parse(filepath)
    root = tree.getroot()
    return from_element(root)

def main() -> None:
    parser = argparse.ArgumentParser(description="Python утилита для отображения дерева каталогов")
    parser.add_argument("directory", nargs='?', default='.', help="Каталог для отображения (по умолчанию: текущий каталог)")
    parser.add_argument("-a", "--all", action="store_true", help="Показать скрытые файлы и каталоги")
    parser.add_argument("-d", "--max-depth", type=int, help="Максимальная глубина отображения")
    parser.add_argument("-s", "--save", help="Сохранить структуру каталога в XML файл")
    parser.add_argument("-l", "--load", help="Загрузить структуру каталога из XML файла")
    args = parser.parse_args()

    if args.load:
        directory_node = load_from_xml(args.load)
        print(f"Структура каталога из файла '{args.load}':")
        print_directory(directory_node)
    else:
        directory: str = args.directory
        show_hidden: bool = args.all
        max_depth: Optional[int] = args.max_depth

        if not os.path.isdir(directory):
            print(f"Ошибка: '{directory}' не является каталогом.")
            return

        directory_node = list_files(directory, show_hidden, max_depth=max_depth)
        print(f"Структура каталога для '{directory}':")
        print_directory(directory_node)

        if args.save:
            save_to_xml(directory_node, args.save)
            print(f"Структура каталога сохранена в файл '{args.save}'")

if __name__ == "__main__":
    main()
