import glob
import re
from os.path import join as pjoin
from pathlib import Path

from tree_sitter import Language, Parser

RUST_LANGUAGE = Language('/home/riv3r/auto-code-rover/build/my-languages.so', 'rust')

def is_test_file(file_path: str) -> bool:
    """Check if a file is a test file.

    This is a simple heuristic to check if a file is a test file.
    """
    return (
        "test" in Path(file_path).parts
        or "tests" in Path(file_path).parts
        or file_path.endswith("_test.rs")
    )

def find_python_files(dir_path: str) -> list[str]:
    """递归获取目录下的所有 .rs 文件。

    排除测试文件。

    Args:
        dir_path (str): 目录路径。

    Returns:
        List[str]: .rs 文件的绝对路径列表。
    """

    rs_files = glob.glob(pjoin(dir_path, "**/*.rs"), recursive=True)
    res = []
    for file in rs_files:
        rel_path = file[len(dir_path) + 1 :]
        if is_test_file(rel_path):
            continue
        res.append(file)
    return res

def parse_python_file(file_path: str) -> dict:
    """解析 Rust 源文件。

    Args:
        file_path (str): Rust 源文件路径。

    Returns:
        dict: 包含结构体、实现、函数等信息的字典。
    """
    rust_parser = RustParser()
    return rust_parser.extract_structs_and_functions(file_path)

class RustParser:
    def __init__(self):
        self.parser = Parser()
        self.parser.set_language(RUST_LANGUAGE)

    def parse_file(self, file_path: str):
        with open(file_path, 'rb') as f:
            source_code = f.read()
        tree = self.parser.parse(source_code)
        return tree

    def extract_structs_and_functions(self, file_path: str):
        tree = self.parse_file(file_path)
        source_code = Path(file_path).read_text()
        root_node = tree.root_node

        structs = []
        impls = {}
        functions = []
        # 键为 (struct_name, start_line, end_line)，值为 trait 名称列表
        struct_relation_map = {}

        def get_text(node):
            return source_code[node.start_byte:node.end_byte]

        def traverse(node):
            if node.type == 'struct_item':
                struct_name = None
                for child in node.children:
                    if child.type == 'type_identifier':
                        struct_name = get_text(child)
                        break
                if struct_name:
                    start_line = node.start_point[0] + 1
                    end_line = node.end_point[0] + 1
                    structs.append((struct_name, start_line, end_line))
                    impls[struct_name] = []
                    struct_relation_map[(struct_name, start_line, end_line)] = []
            elif node.type == 'function_item' and node.parent.type != 'impl_item':
                # 顶层函数
                func_name = None
                for child in node.children:
                    if child.type == 'identifier':
                        func_name = get_text(child)
                        break
                if func_name:
                    start_line = node.start_point[0] + 1
                    end_line = node.end_point[0] + 1
                    functions.append((func_name, start_line, end_line))
            elif node.type == 'impl_item':
                # impl 块
                struct_name = None
                for child in node.children:
                    if child.type == 'type_identifier':
                        struct_name = get_text(child)
                    elif child.type == 'trait_type':
                        # 获取实现的 trait 名称
                        trait_name = get_text(child.child_by_field_name('name'))
                        if struct_name:
                            # 记录结构体与 trait 的关系
                            struct_relation_map.setdefault((struct_name, 0, 0), []).append(trait_name)
                if struct_name:
                    for child in node.children:
                        if child.type == 'function_item':
                            func_name = None
                            for grandchild in child.children:
                                if grandchild.type == 'identifier':
                                    func_name = get_text(grandchild)
                                    break
                            if func_name:
                                start_line = child.start_point[0] + 1
                                end_line = child.end_point[0] + 1
                                impls.setdefault(struct_name, []).append((func_name, start_line, end_line))
            # 递归子节点
            for child in node.children:
                traverse(child)

        traverse(root_node)
        return structs, impls, functions, struct_relation_map

def get_code_snippets(
    file_full_path: str, start: int, end: int, with_lineno=True
) -> str:
    with open(file_full_path) as f:
        file_content = f.readlines()
    snippet = ""
    for i in range(start - 1, end):
        if i < 0 or i >= len(file_content):
            continue
        if with_lineno:
            snippet += f"{i+1} {file_content[i]}"
        else:
            snippet += file_content[i]
    return snippet

def get_code_region_containing_code(
    file_full_path: str, code_str: str, with_lineno=True
) -> list[tuple[int, str]]:
    with open(file_full_path) as f:
        file_content = f.read()

    context_size = 3
    pattern = re.compile(re.escape(code_str))
    occurrences = []
    for match in pattern.finditer(file_content):
        matched_start_pos = match.start()
        matched_line_no = file_content.count("\n", 0, matched_start_pos)

        file_content_lines = file_content.splitlines()

        window_start_index = max(0, matched_line_no - context_size)
        window_end_index = min(
            len(file_content_lines), matched_line_no + context_size + 1
        )

        if with_lineno:
            context = ""
            for i in range(window_start_index, window_end_index):
                context += f"{i+1} {file_content_lines[i]}\n"
        else:
            context = "\n".join(file_content_lines[window_start_index:window_end_index])
        occurrences.append((matched_line_no + 1, context))  # 行号调整为 1-based

    return occurrences

def get_struct_signature(file_full_path: str, struct_name: str) -> str:
    rust_parser = RustParser()
    structs, _, _, _ = rust_parser.extract_structs_and_functions(file_full_path)

    for name, start_line, end_line in structs:
        if name == struct_name:
            return get_code_snippets(file_full_path, start_line, end_line)
    return ""

def get_code_region_around_line(
    file_full_path: str, line_no: int, window_size: int = 10, with_lineno=True
) -> str | None:
    with open(file_full_path) as f:
        file_content = f.readlines()

    if line_no < 1 or line_no > len(file_content):
        return None

    start = max(1, line_no - window_size)
    end = min(len(file_content), line_no + window_size)
    snippet = ""
    for i in range(start - 1, end):
        if with_lineno:
            snippet += f"{i+1} {file_content[i]}"
        else:
            snippet += file_content[i]
    return snippet
