#!/usr/bin/env python3
"""
config_parser.py

Инструмент командной строки для парсинга учебного конфигурационного языка и преобразования его в YAML.

Использование:
    python3 config_parser.py --input путь_к_файлу
"""

import argparse
import re
import sys
import yaml

class ParseError(Exception):
    """Кастомное исключение для ошибок парсинга."""
    def __init__(self, message, line_number=None):
        if line_number:
            super().__init__(f"Line {line_number}: {message}")
        else:
            super().__init__(message)

class ConfigParser:
    def __init__(self):
        self.constants = {}
        self.current_line = 0
        self.lines = []

    def parse(self, text):
        self.lines = text.split('\n')
        self.current_line = 0
        # Пропускаем строки до первой открывающей скобки '{'
        while self.current_line < len(self.lines):
            line = self.lines[self.current_line].strip()
            if not line or line.startswith("*>"):
                self.current_line += 1
                continue
            elif line.startswith("def"):
                self.parse_constant_declaration(line)
            elif line.startswith("{"):
                self.current_line += 1  # Переходим на следующую строку после '{'
                config = self.parse_block()
                # После закрывающей скобки проверяем, нет ли лишнего содержимого
                while self.current_line < len(self.lines):
                    line = self.lines[self.current_line].strip()
                    if not line or line.startswith("*>"):
                        self.current_line += 1
                        continue
                    else:
                        raise ParseError("Ожидался конец файла после закрывающей скобки.", self.current_line + 1)
                return config
            else:
                raise ParseError("Ожидалась открывающая скобка '{'.", self.current_line + 1)
        # Если дошли до конца без нахождения '{', возвращаем пустой словарь
        return {}

    def parse_block(self):
        """
        Парсит блок конфигурации, возможно, вложенный словарь.
        """
        config = {}
        while self.current_line < len(self.lines):
            line = self.lines[self.current_line].strip()
            if not line or line.startswith("*>"):
                # Игнорируем пустые строки и комментарии
                self.current_line += 1
                continue
            elif line.startswith("def"):
                self.parse_constant_declaration(line)
            elif line.startswith("{"):
                # Начало вложенного словаря, рекурсивный вызов
                self.current_line += 1  # Переходим на следующую строку
                nested = self.parse_block()
                # В текущей реализации вложенные словари уже добавляются через parse_entry
                # Поэтому просто добавляем их к текущему словарю
                return nested
            elif line.startswith("}"):
                # Конец текущего блока
                if line not in ["}.", "}"]:
                    raise ParseError("Ожидался конец вложенного словаря с точкой.", self.current_line +1)
                self.current_line +=1
                break
            else:
                self.parse_entry(config, line)
                self.current_line += 1
        return config

    def parse_constant_declaration(self, line):
        """
        Парсит объявление константы вида:
        def имя = значение;
        """
        # Обновлённое регулярное выражение для имен с подчеркиванием и цифрами
        pattern = r'^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+);$'
        match = re.match(pattern, line)
        if not match:
            raise ParseError("Некорректное объявление константы.", self.current_line + 1)
        name, value = match.groups()
        parsed_value = self.parse_value(value.strip())
        self.constants[name] = parsed_value
        self.current_line += 1  # Переходим на следующую строку после объявления

    def parse_entry(self, current_dict, line):
        """
        Парсит строку словаря вида:
        имя -> значение.
        Или:
        имя -> {
            ...
        }.
        """
        # Сначала пытаемся сопоставить стандартный формат "key -> value."
        pattern = r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*->\s*(.+)\.$'
        match = re.match(pattern, line)
        if match:
            key, value = match.groups()
            parsed_value = self.parse_value(value.strip())
            current_dict[key] = parsed_value
            return

        # Затем пытаемся сопоставить формат "key -> {"
        pattern_nested = r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*->\s*\{$'
        match_nested = re.match(pattern_nested, line)
        if match_nested:
            key = match_nested.group(1)
            self.current_line += 1  # Переходим на следующую строку после '{'
            nested_config = self.parse_block()
            current_dict[key] = nested_config
            return

        # Если ни одно из вышеуказанных, выбрасываем ошибку
        raise ParseError("Некорректная запись словаря.", self.current_line +1)

    def parse_value(self, value):
        """
        Парсит значение, которое может быть числом, строкой или словарем.
        """
        if value.startswith('[[') and value.endswith(']]'):
            return self.parse_string(value)
        elif value.startswith('{') and value.endswith('}'):
            return self.parse_dict(value)
        elif value.startswith('|') and value.endswith('|'):
            return self.parse_constant(value)
        else:
            return self.parse_number(value)

    def parse_string(self, value):
        """
        Парсит строку вида [[Это строка]]
        """
        return value[2:-2]

    def parse_number(self, value):
        """
        Парсит числовое значение.
        """
        if re.match(r'^-?\d+(\.\d+)?$', value):
            if '.' in value:
                return float(value)
            else:
                return int(value)
        else:
            raise ParseError(f"Неверный формат числа: {value}", self.current_line +1)

    def parse_dict(self, value):
        """
        Парсит вложенный словарь.
        """
        dict_content = value[1:-1].strip()
        # Создаём временный парсер для вложенного словаря
        nested_parser = ConfigParser()
        # Передаём текущие константы в вложенный парсер
        nested_parser.constants = self.constants.copy()
        # Задаём строки вложенного словаря
        nested_parser.lines = dict_content.split('\n')
        nested_parser.current_line = 0
        return nested_parser.parse_block()

    def parse_constant(self, value):
        """
        Парсит использование константы вида |имя|
        """
        const_name = value[1:-1]
        if const_name not in self.constants:
            raise ParseError(f"Неопределенная константа: {const_name}", self.current_line +1)
        return self.constants[const_name]

def main():
    parser = argparse.ArgumentParser(description='Инструмент для парсинга конфигурационных файлов и преобразования их в YAML.')
    parser.add_argument('--input', '-i', required=True, help='Путь к входному конфигурационному файлу.')

    args = parser.parse_args()

    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Ошибка: Файл {args.input} не найден.", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Ошибка при чтении файла {args.input}: {e}", file=sys.stderr)
        sys.exit(1)

    parser = ConfigParser()
    try:
        config = parser.parse(content)
    except ParseError as pe:
        print(f"Синтаксическая ошибка: {pe}", file=sys.stderr)
        sys.exit(1)

    # Преобразуем в YAML и выводим на stdout
    try:
        yaml_output = yaml.dump(config, sort_keys=False, allow_unicode=True)
        print(yaml_output)
    except yaml.YAMLError as ye:
        print(f"Ошибка при генерации YAML: {ye}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
