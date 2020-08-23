import os
from pathlib import Path
from typing import List

import typer
from jinja2 import Environment, FileSystemLoader
from redbaron import RedBaron

from pytest_codegen.types import FileInfo, FunctionInfo, ArgumentInfo

app = typer.Typer()
env = None


@app.command()
def main(package: str, test_dir: str = "./tests/unittests") -> None:
    package_path = Path(package).resolve()
    test_dir_path = Path(test_dir).resolve()

    files = _collect_files(package_path)
    file_infos = _collect_information(files, package_path, test_dir_path)
    _create_directories(file_infos)
    _create_files(file_infos)
    _write_files(file_infos)


def _write_files(files: List[FileInfo]) -> None:
    function_template = _get_environment().get_template("function.template")
    import_template = _get_environment().get_template("import.template")
    for file in files:

        with open(file["test_path"] / file["test_name"], "r") as f:
            root = RedBaron(f.read() or '"""Test module."""\n')

        existing_functions = [function.name for function in root.find_all("def")]

        for function in file["functions"]:
            if f"test_{function['name']}" not in existing_functions:
                root.extend(["\n", "\n"])
                root.append(function_template.render(**function))

        root.insert(1, import_template.render(**file))
        root.insert(1, "import pytest")

        with open(file["test_path"] / file["test_name"], "w") as f:
            f.write(root.dumps())


def _create_files(files: List[FileInfo]) -> None:
    for file in files:
        try:
            with open(file["test_path"] / file["test_name"], "x"):
                pass
        except FileExistsError:
            pass


def _create_directories(files: List[FileInfo]) -> None:
    for file in files:
        if not os.path.exists(file["test_path"]):
            os.makedirs(file["test_path"], exist_ok=True)


def _get_environment() -> Environment:
    global env
    if not env:
        loader = FileSystemLoader(searchpath=Path(__file__).parent / Path("templates"))
        env = Environment(loader=loader)
    return env


def _collect_information(
    files: List[Path], base_path: Path, test_dir_path: Path
) -> List[FileInfo]:
    file_info_list = []
    for file in files:
        file_info = FileInfo(
            name=file.name,
            module=file.name.split(".")[0],
            package=".".join(
                os.path.relpath(file, base_path.parent)[:-3].split(os.sep)
            ),
            path=file.parent,
            test_path=test_dir_path / Path(os.path.relpath(file, base_path)).parent,
            functions=[],
        )  # type: ignore

        file_info["test_name"] = (
            _get_environment().get_template("filename.template").render(**file_info)
        )

        root_fst = RedBaron(file.read_text())

        # collect function information
        for function in root_fst.find_all("def"):

            # TODO: properly find below fields
            function_info = FunctionInfo(
                name=function.name,
                is_private=function.name.startswith("_"),
                docstring=function[0].find("string"),
                return_type=str(function.return_annotation.value),
                arguments=[],
            )

            #  collect function's argument information
            for argument in function.arguments:
                argument_info = ArgumentInfo(
                    name=str(argument.name),
                    default=argument.value.value
                    if argument.value is not None
                    else None,
                    type=argument.annotation.value
                    if argument.annotation is not None
                    else None,
                )
                function_info["arguments"].append(argument_info)

            file_info["functions"].append(function_info)
        if file_info["functions"]:
            file_info_list.append(file_info)

    return file_info_list


def _collect_files(path: Path) -> List[Path]:
    """Collect all .py files in a package."""
    files_list: List = []
    if os.path.isdir(path):
        files = os.listdir(path)
        for file in files:
            files_list.extend(_collect_files((Path(path) / file).absolute()))
    else:
        if path.name.endswith(".py") and not path.name.startswith("__"):
            files_list.append(Path(path).absolute())

    return files_list
