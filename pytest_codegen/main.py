import os
from pathlib import Path
from typing import List, Dict, Generator

import typer
from redbaron import RedBaron

app = typer.Typer()


@app.command()
def main(package: str, test_dir: str = "./tests/unittests") -> None:
    path = Path(package).resolve()
    test_path = Path(test_dir).resolve()

    files = (x for x in _collect_files(path))
    analyzed_files = _analyze(files)

    for af in analyzed_files:
        test_file = os.path.relpath(af['original_file'], path)
        af['test_file'] = test_path / test_file
        pack = test_file[:-3].split(os.sep)
        pack.insert(0, bytes(package))
        af['package'] = ".".join(pack)

    _create_test_files(analyzed_files)
    _write_test_functions(analyzed_files)


def _create_test_files(analyzed_files) -> None:
    for file in analyzed_files:
        if not os.path.exists(file['test_file'].parent):
            os.makedirs(file['test_file'].parent, exist_ok=True)


def _write_test_functions(analyzed_files) -> None:
    for file in analyzed_files:
        try:
            with open(file['test_file'], 'x'):
                pass
        except FileExistsError:
            pass

        with open(file['test_file'], 'r') as f:
            root = RedBaron(f.read() or f'"""tests for {file["package"]}."""\n')

        existing = [node for node in root.find_all('def')]
        found = {function['test_name']: function for function in file['functions']}
        to_write = set(found) - set(existing)

        for func in to_write:
            root.extend(["\n", "\n"])
            func_node = RedBaron(f"def {found[func]['test_name']}():\n\tpass")
            func_node[0].insert(0, "#  TODO: write test")
            func_node[0].insert(1, f"#  assert {found[func]['name']}()")
            root.append(func_node.dumps())

        with open(file['test_file'], "w") as f:
            f.write(root.dumps())


def _analyze(files: Generator[Path]) -> List[Dict]:
    analyzed_files = []
    for file in files:

        analyzed_file = dict(
            original_file=file
        )

        with open(file, "r") as f:
            root = RedBaron(f.read())
            functions = root.find_all('def')

            analyzed_file['functions'] = [dict(
                name=func.name,
                test_name=f"test_{func.name}",
                arguments=[str(arg.name) for arg in func.arguments]
            ) for func in functions if not func.name.startswith("_")]

        if analyzed_file.get('functions', []):
            analyzed_files.append(analyzed_file)
    return analyzed_files


def _collect_files(path: Path) -> Generator[Path]:
    if os.path.isdir(path):
        files = os.listdir(path)
        for file in files:
            yield from _collect_files((Path(path) / file).absolute())
    else:
        if path.name.endswith(".py") and not path.name.startswith("__"):
            yield Path(path).absolute()
