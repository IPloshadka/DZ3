#!/usr/bin/env python3
"""
test_config_parser.py

Модульные тесты для config_parser.py.
"""

import unittest
from config_parser import ConfigParser, ParseError
import yaml

class TestConfigParser(unittest.TestCase):
    def setUp(self):
        self.parser = ConfigParser()

    def test_empty_file(self):
        content = ""
        expected = {}
        result = self.parser.parse(content)
        self.assertEqual(result, expected)

    def test_only_comments(self):
        content = "*> Это комментарий\n*> Еще комментарий"
        expected = {}
        result = self.parser.parse(content)
        self.assertEqual(result, expected)

    def test_single_entry(self):
        content = "{\n    key1 -> 123.\n}."
        expected = {"key1": 123}
        result = self.parser.parse(content)
        self.assertEqual(result, expected)

    def test_multiple_entries(self):
        content = "{\n    key1 -> 123.\n    key2 -> [[Строка]].\n    key3 -> 45.67.\n}."
        expected = {
            "key1": 123,
            "key2": "Строка",
            "key3": 45.67
        }
        result = self.parser.parse(content)
        self.assertEqual(result, expected)

    def test_nested_dictionary(self):
        content = "{\n    parent -> {\n        child1 -> 1.\n        child2 -> [[Value]].\n    }.\n}."
        expected = {
            "parent": {
                "child1": 1,
                "child2": "Value"
            }
        }
        result = self.parser.parse(content)
        self.assertEqual(result, expected)

    def test_constant_declaration_and_usage(self):
        content = """
def CONST = [[Константа]];
{
    key1 -> |CONST|.
}."""
        expected = {
            "key1": "Константа"
        }
        result = self.parser.parse(content)
        self.assertEqual(result, expected)

    def test_constant_overwrite(self):
        content = """
def CONST = 100;
def CONST = 200;
{
    key1 -> |CONST|.
}."""
        expected = {
            "key1": 200
        }
        result = self.parser.parse(content)
        self.assertEqual(result, expected)

    def test_undefined_constant_usage(self):
        content = """
{
    key1 -> |UNDEFINED|.
}."""
        with self.assertRaises(ParseError) as context:
            self.parser.parse(content)
        self.assertIn("Неопределенная константа: UNDEFINED", str(context.exception))

    def test_invalid_constant_declaration(self):
        content = "def123 = 456;.\n{ key1 -> 456. }."
        with self.assertRaises(ParseError) as context:
            self.parser.parse(content)
        self.assertIn("Некорректное объявление константы.", str(context.exception))

    def test_invalid_entry_syntax(self):
        content = "{\n    key1 => 123.\n}."
        with self.assertRaises(ParseError) as context:
            self.parser.parse(content)
        self.assertIn("Некорректная запись словаря.", str(context.exception))

    def test_invalid_number(self):
        content = "{\n    key1 -> 12a3.\n}."
        with self.assertRaises(ParseError) as context:
            self.parser.parse(content)
        self.assertIn("Неверный формат числа: 12a3", str(context.exception))

    def test_example_network_configuration(self):
        content = """
*> Конфигурация сети
def IP = [[192.168.1.1]];
{
    hostname -> [[server]].
    ip_address -> |IP|.
    services -> {
        http -> 80.
        https -> 443.
        ssh -> 22.
    }.
}."""
        expected = {
            "hostname": "server",
            "ip_address": "192.168.1.1",
            "services": {
                "http": 80,
                "https": 443,
                "ssh": 22
            }
        }
        result = self.parser.parse(content)
        self.assertEqual(result, expected)

    def test_example_application_configuration(self):
        content = """
*> Конфигурация приложения
def VERSION = [[1.0.0]];
def PORT = 8080;
{
    app_name -> [[MyApp]].
    version -> |VERSION|.
    port -> |PORT|.
    database -> {
        host -> [[localhost]].
        port -> 5432.
        user -> [[admin]].
        password -> [[secret]].
    }.
}."""
        expected = {
            "app_name": "MyApp",
            "version": "1.0.0",
            "port": 8080,
            "database": {
                "host": "localhost",
                "port": 5432,
                "user": "admin",
                "password": "secret"
            }
        }
        result = self.parser.parse(content)
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
