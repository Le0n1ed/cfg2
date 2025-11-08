import yaml
import json
import requests


class DependencyAnalyzer:
    def __init__(self, config_file="config.yaml"):
        self.config = self.load_config(config_file)
        self.dependency_graph = {}

    def load_config(self, config_file):
        """Этап 1: Загрузка конфигурации из YAML"""
        try:
            with open(config_file, 'r') as file:
                config = yaml.safe_load(file)

            # Проверяем обязательные параметры
            required = ['package_name', 'repository_url', 'mode', 'version', 'output_file', 'max_depth']
            for param in required:
                if param not in config:
                    raise ValueError(f"Не хватает параметра: {param}")

            # Выводим все параметры
            print("=== Конфигурационные параметры ===")
            for key, value in config.items():
                print(f"{key}: {value}")

            return config

        except FileNotFoundError:
            raise FileNotFoundError(f"Файл {config_file} не найден")
        except yaml.YAMLError as e:
            raise ValueError(f"Ошибка в YAML файле: {e}")

    def get_package_info(self, package_name, version):
        """Этап 2: Получение информации о пакете"""
        if self.config['mode'] == 'test':
            # Тестовый режим - читаем из файла
            try:
                with open(self.config['repository_url'], 'r') as file:
                    test_data = json.load(file)
                return test_data.get(package_name, {})
            except FileNotFoundError:
                raise FileNotFoundError("Тестовый файл не найден")
        else:
            # Режим работы с npm репозиторием
            url = f"{self.config['repository_url']}/{package_name}"
            response = requests.get(url)
            if response.status_code == 200:
                package_data = response.json()
                versions = package_data.get('versions', {})
                if version in versions:
                    return versions[version]
                else:
                    # Если версия не найдена, берем первую доступную
                    first_version = list(versions.keys())[0] if versions else None
                    if first_version:
                        return versions[first_version]
            raise ValueError(f"Не удалось получить информацию о пакете {package_name}")

    def get_direct_dependencies(self, package_name, version):
        """Этап 2: Получение прямых зависимостей"""
        package_info = self.get_package_info(package_name, version)
        dependencies = package_info.get('dependencies', {})

        # Выводим прямые зависимости
        print(f"\n=== Прямые зависимости {package_name}@{version} ===")
        for dep, ver in dependencies.items():
            print(f"{dep}: {ver}")

        return dependencies

    def build_dependency_graph(self, package_name, version, depth=0, path=None):
        """Этап 3: Построение графа зависимостей с помощью DFS"""
        if path is None:
            path = []

        # Проверка максимальной глубины
        if depth > self.config['max_depth']:
            return

        # Проверка циклических зависимостей
        if package_name in path:
            print(f"Обнаружена циклическая зависимость: {' -> '.join(path + [package_name])}")
            return

        current_path = path + [package_name]

        # Получаем зависимости текущего пакета
        dependencies = self.get_direct_dependencies(package_name, version)
        self.dependency_graph[package_name] = dependencies

        # Рекурсивно обрабатываем зависимости
        for dep_name, dep_version in dependencies.items():
            if dep_name not in self.dependency_graph:
                self.build_dependency_graph(dep_name, dep_version, depth + 1, current_path)

    def run_analysis(self):
        """Запуск всего анализа"""
        print("🚀 Запуск анализа зависимостей...")

        # Этап 3: Строим граф зависимостей
        self.build_dependency_graph(
            self.config['package_name'],
            self.config['version']
        )

        # Выводим итоговый граф
        print(f"\n=== Итоговый граф зависимостей ===")
        for package, deps in self.dependency_graph.items():
            print(f"{package}: {list(deps.keys())}")


def main():
    try:
        analyzer = DependencyAnalyzer()
        analyzer.run_analysis()
    except Exception as e:
        print(f" Ошибка: {e}")


if __name__ == "__main__":
    main()