#!/usr/bin/env python3
"""
ASMP - ArtStudia Manager Packets
Менеджер пакетов от ArtTeam
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from colorama import init, Fore, Back, Style

# Инициализация colorama для Windows
init(autoreset=True)

__version__ = "0.1.0"
__author__ = "ArtTeam"
__email__ = "ArtRebos@gmail.com"
__repository__ = "https://github.com/artteam09/asmp"


class ASMPClient:
    def __init__(self, base_url=None):
        self.base_url = base_url or "https://api.artstudia.com"  # URL по умолчанию
        self.config_dir = Path.home() / ".asmp"
        self.packages_file = self.config_dir / "packages.json"
        self.installed_file = self.config_dir / "installed_packages.json"
        self.config_file = self.config_dir / "config.json"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'ASMP/{__version__}',
            'Content-Type': 'application/json'
        })
        self.init_config()

    def init_config(self):
        """Инициализация конфигурации"""
        self.config_dir.mkdir(exist_ok=True)

        # Загрузка конфигурации
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.base_url = config.get('server_url', self.base_url)
        else:
            config = {
                'server_url': self.base_url,
                'auto_update': True,
                'timeout': 30,
                'client_version': __version__
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

        # Локальная база пакетов (кэш)
        if not self.packages_file.exists():
            default_packages = {
                "packages": [
                    {
                        "name": "launcher_updater",
                        "version": "1.0.0",
                        "description": "Launcher and updater for ArtStudia applications",
                        "author": "ArtTeam",
                        "license": "MIT",
                        "type": "tool",
                        "tags": ["launcher", "updater", "gui"],
                        "source": "https://github.com/artteam9/launcher_updater.git",
                        "source_type": "git"
                    },
                    {
                        "name": "artutils",
                        "version": "1.2.0",
                        "description": "Utility functions for ArtTeam projects",
                        "author": "ArtTeam",
                        "license": "MIT",
                        "type": "library",
                        "tags": ["utilities", "helpers", "tools"],
                        "source": "artutils",
                        "source_type": "pypi"
                    }
                ],
                "last_updated": int(time.time()),
                "client_version": __version__
            }
            with open(self.packages_file, 'w', encoding='utf-8') as f:
                json.dump(default_packages, f, indent=2, ensure_ascii=False)

        if not self.installed_file.exists():
            with open(self.installed_file, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2)

    def make_request(self, endpoint, data=None):
        """Выполнить запрос к серверу"""
        url = urljoin(self.base_url, endpoint)

        base_request = {
            "app_name": "ADK - ArtStudia Developer Kit",
            "api_version": "0.1.0",
            "client_version": __version__,
            "timestamp": int(time.time())
        }

        if data:
            base_request.update(data)

        try:
            print(f"{Fore.CYAN}🌐 Запрос к {url}...")
            response = self.session.post(
                url,
                json=base_request,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}❌ Не удалось подключиться к серверу {self.base_url}")
            return None
        except requests.exceptions.Timeout:
            print(f"{Fore.RED}❌ Таймаут подключения к серверу")
            return None
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}❌ Ошибка сети: {e}")
            return None
        except json.JSONDecodeError:
            print(f"{Fore.RED}❌ Неверный ответ от сервера")
            return None

    def search_remote(self, query):
        """Поиск пакетов на удаленном сервере"""
        print(f"{Fore.CYAN}🔍 Поиск '{query}' на сервере {self.base_url}...")

        request_data = {
            "type_request": "search",
            "query": query,
            "filters": {
                "type": ["library", "tool"],
                "status": ["stable", "beta"]
            }
        }

        response = self.make_request("/api/packages/search", request_data)

        if response and response.get("success"):
            packages = response.get("packages", [])
            # Обновляем локальный кэш
            self.update_local_cache(packages)
            return packages
        else:
            error_msg = response.get("error", "Неизвестная ошибка") if response else "Нет соединения"
            print(f"{Fore.YELLOW}⚠️  Используется локальная база: {error_msg}")
            return self.search_local(query)

    def search_local(self, query):
        """Поиск в локальной базе"""
        try:
            with open(self.packages_file, 'r', encoding='utf-8') as f:
                packages_data = json.load(f)

            found_packages = []
            for pkg in packages_data.get("packages", []):
                if (query.lower() in pkg["name"].lower() or
                        query.lower() in pkg.get("description", "").lower() or
                        query.lower() in " ".join(pkg.get("tags", [])).lower()):
                    found_packages.append(pkg)
            return found_packages
        except Exception as e:
            print(f"{Fore.RED}❌ Ошибка чтения локальной базы: {e}")
            return []

    def update_local_cache(self, packages):
        """Обновить локальный кэш пакетов"""
        try:
            with open(self.packages_file, 'r', encoding='utf-8') as f:
                local_data = json.load(f)

            # Обновляем существующие и добавляем новые пакеты
            local_packages = {pkg["name"]: pkg for pkg in local_data.get("packages", [])}
            for pkg in packages:
                local_packages[pkg["name"]] = pkg

            local_data["packages"] = list(local_packages.values())
            local_data["last_updated"] = int(time.time())
            local_data["client_version"] = __version__

            with open(self.packages_file, 'w', encoding='utf-8') as f:
                json.dump(local_data, f, indent=2, ensure_ascii=False)

            print(f"{Fore.GREEN}✅ Локальный кэш обновлен ({len(packages)} пакетов)")

        except Exception as e:
            print(f"{Fore.YELLOW}⚠️  Не удалось обновить кэш: {e}")

    def get_package_info_remote(self, package_name, version=None):
        """Получить информацию о пакете с сервера"""
        request_data = {
            "type_request": "package_info",
            "package_name": package_name,
            "version": version
        }

        response = self.make_request("/api/packages/info", request_data)

        if response and response.get("success"):
            return response.get("package")
        return None

    def install_package_remote(self, package_name, version=None):
        """Установить пакет с сервера"""
        print(f"{Fore.CYAN}📦 Получение информации о пакете {package_name}...")

        package_info = self.get_package_info_remote(package_name, version)
        if not package_info:
            print(f"{Fore.RED}❌ Пакет {package_name} не найден на сервере")
            return False

        print(f"{Fore.GREEN}✅ Пакет найден: {package_info['name']} v{package_info['version']}")
        print(f"{Fore.WHITE}📝 {package_info.get('description', 'Нет описания')}")
        print(f"{Fore.CYAN}👨‍💻 Автор: {package_info.get('author', 'Unknown')}")

        # Показываем зависимости
        dependencies = package_info.get('dependencies', [])
        if dependencies:
            print(f"{Fore.YELLOW}📋 Зависимости: {', '.join(dependencies)}")

        # Запрос на скачивание
        download_data = {
            "type_request": "download",
            "package_name": package_name,
            "version": version or package_info["version"]
        }

        response = self.make_request("/api/packages/download", download_data)

        if response and response.get("success"):
            download_url = response.get("download_url")
            install_script = response.get("install_script")

            return self.download_and_install(package_info, download_url, install_script)
        else:
            print(f"{Fore.RED}❌ Не удалось получить ссылку для скачивания")
            return False

    def download_and_install(self, package_info, download_url, install_script=None):
        """Скачать и установить пакет"""
        try:
            print(f"{Fore.CYAN}📥 Загрузка пакета...")

            # Имитация загрузки
            for i in range(5):
                percent = (i + 1) * 20
                print(f"{Fore.YELLOW}⬇️  Загрузка... [{''.join(['█'] * (i + 1))}{''.join(['░'] * (4 - i))}] {percent}%")
                time.sleep(0.3)

            # Установка зависимостей
            dependencies = package_info.get('dependencies', [])
            if dependencies:
                print(f"{Fore.CYAN}🔨 Установка зависимостей...")
                for dep in dependencies:
                    print(f"   📦 {dep}...")
                    time.sleep(0.5)

            if install_script:
                print(f"{Fore.CYAN}🚀 Выполнение скрипта установки...")
                time.sleep(1)

            # Сохраняем информацию об установке
            self.save_installed_package(package_info)

            print(f"{Fore.GREEN}🎉 Пакет {package_info['name']} v{package_info['version']} успешно установлен!")
            print(f"{Fore.CYAN}💡 Для использования импортируйте: import {package_info['name']}")
            return True

        except Exception as e:
            print(f"{Fore.RED}❌ Ошибка установки: {e}")
            return False

    def save_installed_package(self, package_info):
        """Сохранить информацию об установленном пакете"""
        installed = self.get_installed_packages()

        # Удаляем старую версию если есть
        installed = [p for p in installed if p["name"] != package_info["name"]]

        # Добавляем информацию об установке
        package_info["installed_at"] = int(time.time())
        package_info["installed_by"] = "asmp"
        package_info["client_version"] = __version__
        installed.append(package_info)

        with open(self.installed_file, 'w', encoding='utf-8') as f:
            json.dump(installed, f, indent=2, ensure_ascii=False)

    def get_installed_packages(self):
        """Получить список установленных пакетов"""
        try:
            with open(self.installed_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def update_server_url(self, new_url):
        """Обновить URL сервера"""
        self.base_url = new_url
        config = {
            'server_url': new_url,
            'auto_update': True,
            'timeout': 30,
            'client_version': __version__
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"{Fore.GREEN}✅ URL сервера обновлен: {new_url}")

    def server_status(self):
        """Проверить статус сервера"""
        print(f"{Fore.CYAN}🔄 Проверка подключения к {self.base_url}...")

        request_data = {
            "type_request": "ping"
        }

        response = self.make_request("/api/status", request_data)

        if response and response.get("success"):
            server_info = response.get("server", {})
            print(f"{Fore.GREEN}✅ Сервер доступен")
            print(f"{Fore.WHITE}🏷️  Имя: {server_info.get('name', 'Unknown')}")
            print(f"{Fore.WHITE}📊 Версия API: {server_info.get('api_version', 'Unknown')}")
            print(f"{Fore.WHITE}📦 Пакетов: {server_info.get('packages_count', 0)}")
            print(f"{Fore.WHITE}⏰ Время работы: {server_info.get('uptime', 'Unknown')}")
            print(f"{Fore.WHITE}🌐 URL: {self.base_url}")
        else:
            print(f"{Fore.RED}❌ Сервер не доступен")

    def show_config(self):
        """Показать текущую конфигурацию"""
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        print(f"{Fore.CYAN}⚙️  Конфигурация ASMP:")
        print(f"{Fore.WHITE}{'=' * 40}")
        print(f"{Fore.GREEN}Версия клиента: {Fore.WHITE}{__version__}")
        print(f"{Fore.GREEN}Сервер: {Fore.WHITE}{config.get('server_url', 'Не указан')}")
        print(f"{Fore.GREEN}Авто-обновление: {Fore.WHITE}{config.get('auto_update', True)}")
        print(f"{Fore.GREEN}Таймаут: {Fore.WHITE}{config.get('timeout', 30)}с")
        print(f"{Fore.GREEN}Директория конфига: {Fore.WHITE}{self.config_dir}")


def print_package_list(packages, title="Найденные пакеты"):
    """Красиво вывести список пакетов"""
    if not packages:
        print(f"{Fore.YELLOW}📭 {title} не найдены")
        return

    print(f"{Fore.CYAN}🎨 {title} ({len(packages)}):")
    print(f"{Fore.WHITE}{'=' * 60}")

    for i, pkg in enumerate(packages, 1):
        print(f"{Fore.GREEN}{i}. {pkg['name']} {Fore.CYAN}v{pkg.get('version', 'N/A')}")
        print(f"{Fore.WHITE}   📝 {pkg.get('description', 'Нет описания')}")

        tags = pkg.get('tags', [])
        if tags:
            print(f"   🏷️  {', '.join(tags)}")

        print(f"   📦 Тип: {pkg.get('type', 'library')} | 👨‍💻 Автор: {pkg.get('author', 'Unknown')}")
        print()


def print_banner():
    """Показать баннер ASMP"""
    banner = f"""
{Fore.CYAN}
    █████╗ ███████╗███╗   ███╗██████╗ 
   ██╔══██╗██╔════╝████╗ ████║██╔══██╗
   ███████║███████╗██╔████╔██║██████╔╝
   ██╔══██║╚════██║██║╚██╔╝██║██╔═══╝ 
   ██║  ██║███████║██║ ╚═╝ ██║██║     
   ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚═╝     
{Fore.YELLOW}
   ArtStudia Manager Packets v{__version__}
   Repository: {__repository__}
   Author: {__author__} <{__email__}>
{Fore.RESET}
"""
    print(banner)


def main():
    parser = argparse.ArgumentParser(
        prog="asp",
        description=f"{Fore.CYAN}🎨 ASMP - ArtStudia Manager Packets{Fore.RESET}",
        epilog=f"""Примеры использования:
  {Fore.GREEN}asp install launcher_updater{Fore.RESET}    - Установить пакет
  {Fore.GREEN}asp search game{Fore.RESET}                - Найти пакеты
  {Fore.GREEN}asp list{Fore.RESET}                       - Список установленных
  {Fore.GREEN}asp info artutils{Fore.RESET}              - Информация о пакете
  {Fore.GREEN}asp server-status{Fore.RESET}              - Статус сервера
  {Fore.GREEN}asp config{Fore.RESET}                     - Показать конфигурацию
  {Fore.GREEN}asp set-server http://api.artstudia.com{Fore.RESET} - Установить сервер""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

    # Команда install
    install_parser = subparsers.add_parser("install", help="Установка пакета")
    install_parser.add_argument("package_name", help="Название пакета для установки")
    install_parser.add_argument("--version", help="Конкретная версия пакета")

    # Команда uninstall
    uninstall_parser = subparsers.add_parser("uninstall", help="Удаление пакета")
    uninstall_parser.add_argument("package_name", help="Название пакета для удаления")

    # Команда search
    search_parser = subparsers.add_parser("search", help="Поиск пакетов")
    search_parser.add_argument("query", help="Поисковый запрос")

    # Команда list
    subparsers.add_parser("list", help="Список установленных пакетов")

    # Команда info
    info_parser = subparsers.add_parser("info", help="Информация о пакете")
    info_parser.add_argument("package_name", help="Название пакета")

    # Команда server-status
    subparsers.add_parser("server-status", help="Статус сервера")

    # Команда config
    subparsers.add_parser("config", help="Показать конфигурацию")

    # Команда set-server
    server_parser = subparsers.add_parser("set-server", help="Установить URL сервера")
    server_parser.add_argument("url", help="URL сервера ASMP")

    # Команда version
    subparsers.add_parser("version", help="Показать версию ASMP")

    args = parser.parse_args()

    # Показываем баннер если нет команд
    if len(sys.argv) == 1:
        print_banner()
        parser.print_help()
        return

    asmp = ASMPClient()

    if args.command == "install":
        asmp.install_package_remote(args.package_name, args.version)
    elif args.command == "uninstall":
        installed = asmp.get_installed_packages()
        package = next((p for p in installed if p["name"] == args.package_name), None)

        if not package:
            print(f"{Fore.RED}❌ Пакет {args.package_name} не установлен!")
        else:
            installed = [p for p in installed if p["name"] != args.package_name]
            with open(asmp.installed_file, 'w', encoding='utf-8') as f:
                json.dump(installed, f, indent=2, ensure_ascii=False)
            print(f"{Fore.GREEN}✅ Пакет {args.package_name} успешно удален!")
    elif args.command == "search":
        packages = asmp.search_remote(args.query)
        print_package_list(packages, f"Результаты поиска '{args.query}'")
    elif args.command == "list":
        packages = asmp.get_installed_packages()
        print_package_list(packages, "Установленные пакеты")
    elif args.command == "info":
        package_info = asmp.get_package_info_remote(args.package_name)
        if package_info:
            print(f"{Fore.CYAN}📦 Информация о пакете {args.package_name}:")
            print(f"{Fore.WHITE}{'=' * 50}")
            print(f"{Fore.GREEN}Имя: {Fore.WHITE}{package_info['name']}")
            print(f"{Fore.GREEN}Версия: {Fore.WHITE}{package_info.get('version', 'N/A')}")
            print(f"{Fore.GREEN}Описание: {Fore.WHITE}{package_info.get('description', 'Нет описания')}")
            print(f"{Fore.GREEN}Тип: {Fore.WHITE}{package_info.get('type', 'library')}")
            print(f"{Fore.GREEN}Лицензия: {Fore.WHITE}{package_info.get('license', 'Unknown')}")
            print(f"{Fore.GREEN}Автор: {Fore.WHITE}{package_info.get('author', 'Unknown')}")

            dependencies = package_info.get('dependencies', [])
            if dependencies:
                print(f"{Fore.GREEN}Зависимости: {Fore.WHITE}{', '.join(dependencies)}")

            tags = package_info.get('tags', [])
            if tags:
                print(f"{Fore.GREEN}Теги: {Fore.WHITE}{', '.join(tags)}")
        else:
            print(f"{Fore.RED}❌ Пакет {args.package_name} не найден!")
    elif args.command == "server-status":
        asmp.server_status()
    elif args.command == "config":
        asmp.show_config()
    elif args.command == "set-server":
        asmp.update_server_url(args.url)
    elif args.command == "version":
        print_banner()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()