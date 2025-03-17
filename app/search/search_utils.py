import glob
import re
from os.path import join as pjoin
from pathlib import Path
import parser, json
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

def parse_python_file(file_path: str) -> tuple[
    list[tuple[str, int, int]],  # structs: [(struct_name, start_line, end_line)]
    dict[str, list[tuple[str, int, int]]],  # impls: {struct_name: [(method_name, start_line, end_line)]}
    list[tuple[str, int, int]],  # functions: [(func_name, start_line, end_line)]
    # dict[tuple[str, int, int], list[str]],  # struct_relation_map: {(struct_name, start_line, end_line): [trait_names]}
    # list[tuple[str, int, int]]  # traits: [(trait_name, start_line, end_line)]
]:
    """解析 Rust 源文件。

    Args:
        file_path (str): Rust 源文件路径。

    Returns:
        tuple: 包含结构体、实现、函数、trait关系和trait定义的元组。
    """
    if file_path.endswith(".rs"):
        with open(file_path) as fp:
            # 解析Rust文件并存储
            data = json.loads(parser.parse_rust_code(fp.read()))
            structs_meta = data.get("structs", [])
            structs = [(s["name"], s["start_line"], s["end_line"]) for s in structs_meta]
            impls = {}
            for struct in structs_meta:
                impls[struct["name"]] = []
                for method in struct["methods"]:
                    impls[struct["name"]].append((method["name"], method["start_line"], method["end_line"]))
            functions_meta = data.get("functions", [])
            functions = [(f["name"], f["start_line"], f["end_line"]) for f in functions_meta]
            return structs, impls, functions
    else:
        # 处理非Rust文件（此处只记录文件名）
        return None


class RustParser:
    def __init__(self):
        self.parser = Parser()
        self.parser.set_language(RUST_LANGUAGE)

    def print_tree(self, node, level=0, source_code=None):
        """打印AST树结构。
        
        Args:
            node: 要打印的节点
            level: 当前缩进级别
            source_code: 源代码文本，用于显示实际内容
        """
        indent = "  " * level
        node_text = ""
        if source_code:
            node_text = source_code[node.start_byte:node.end_byte]
            if len(node_text) > 50:  # 如果文本太长，截断显示
                node_text = node_text[:47] + "..."
            node_text = f" [{node_text}]"
        
        # 打印节点信息
        print(f"{indent}{node.type}{node_text}")
        
        # 打印字段信息
        if hasattr(node, 'fields'):
            for field_name, field_value in node.fields.items():
                if field_value:
                    if isinstance(field_value, list):
                        for item in field_value:
                            print(f"{indent}  field {field_name}: {item.type}")
                    else:
                        print(f"{indent}  field {field_name}: {field_value.type}")
        
        # 递归打印子节点
        for child in node.children:
            self.print_tree(child, level + 1, source_code)

    def parse_file(self, file_path: str):
        with open(file_path, 'rb') as f:
            source_code = f.read()
        tree = self.parser.parse(source_code)
        return tree

    def print_ast(self, file_path: str):
        """打印整个文件的AST结构。"""
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        tree = self.parser.parse(bytes(source_code, 'utf-8'))
        print(f"\n=== AST for {file_path} ===")
        self.print_tree(tree.root_node, source_code=source_code)
        print("=== End of AST ===\n")

    def extract_structs_and_functions(self, file_path: str) -> tuple[
        list[tuple[str, int, int]],  # structs: [(struct_name, start_line, end_line)]
        dict[str, list[tuple[str, int, int]]],  # impls: {struct_name: [(method_name, start_line, end_line)]}
        list[tuple[str, int, int]],  # functions: [(func_name, start_line, end_line)]
        dict[tuple[str, int, int], list[str]],  # struct_relation_map: {(struct_name, start_line, end_line): [trait_names]}
        list[tuple[str, int, int]]  # traits: [(trait_name, start_line, end_line)]
    ]:
        tree = self.parse_file(file_path)
        source_code = Path(file_path).read_text()
        root_node = tree.root_node
        structs = []
        impls = {}
        functions = []
        traits = []  # 新增：存储trait定义
        struct_relation_map = {}

        def get_text(node):
            return source_code[node.start_byte:node.end_byte]

        def is_top_level_function(node):
            """检查一个函数节点是否为顶层函数。
            
            通过向上遍历父节点，确保该函数不在任何impl块或trait定义内。
            """
            current = node
            while current.parent is not None:
                if current.parent.type in ['impl_item', 'trait_item']:
                    return False
                current = current.parent
            return True

        # 首先遍历一次找出所有结构体并初始化impls字典
        def init_structs(node):
            if node.type == 'struct_item':
                for child in node.children:
                    if child.type == 'type_identifier':
                        struct_name = get_text(child)
                        if struct_name:
                            impls[struct_name] = []
                            break
            for child in node.children:
                init_structs(child)

        # 先初始化impls字典
        init_structs(root_node)

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
                    struct_relation_map[(struct_name, start_line, end_line)] = []
            elif node.type == 'trait_item':  # 新增：处理trait定义
                trait_name = None
                for child in node.children:
                    if child.type == 'type_identifier':
                        trait_name = get_text(child)
                        break
                if trait_name:
                    start_line = node.start_point[0] + 1
                    end_line = node.end_point[0] + 1
                    traits.append((trait_name, start_line, end_line))
            elif node.type == 'function_item':
                # 检查是否为顶层函数
                if is_top_level_function(node):
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
                trait_name = None
                impl_functions = []
                is_trait_impl = False

                # print("Processing impl block...")
                # 第一遍遍历：收集struct_name和trait_name
                for child in node.children:
                    # print(f"Child type: {child.type}")
                    if child.type == 'type_identifier':
                        if not is_trait_impl:
                            # 第一次遇到type_identifier，可能是trait名称或struct名称
                            if struct_name is None:
                                struct_name = get_text(child)
                                # print(f"Found first type_identifier: {struct_name}")
                        else:
                            # 已经遇到了for关键字，这是struct名称
                            struct_name = get_text(child)
                            # print(f"Found struct name in trait impl: {struct_name}")
                    elif child.type == 'for':
                        is_trait_impl = True
                        # 之前存的struct_name实际上是trait名称
                        trait_name = struct_name
                        struct_name = None
                        # print(f"Found trait name: {trait_name}")
                    elif child.type == 'declaration_list':
                        # print("Processing declaration_list")
                        # 处理declaration_list中的函数
                        for decl in child.children:
                            if decl.type == 'function_item':
                                func_name = None
                                for grandchild in decl.children:
                                    if grandchild.type == 'identifier':
                                        func_name = get_text(grandchild)
                                        break
                                if func_name:
                                    start_line = decl.start_point[0] + 1
                                    end_line = decl.end_point[0] + 1
                                    impl_functions.append((func_name, start_line, end_line))
                                    # print(f"Found impl function: {func_name}")

                # print(f"After processing impl block - struct_name: {struct_name}, trait_name: {trait_name}, functions: {impl_functions}")
                # 处理收集到的信息
                if struct_name:
                    if trait_name:
                        # 记录结构体与 trait 的关系
                        # 从structs列表中找到对应struct的start_line和end_line
                        struct_start_line = 0
                        struct_end_line = 0
                        for s_name, s_start, s_end in structs:
                            if s_name == struct_name:
                                struct_start_line = s_start
                                struct_end_line = s_end
                                break
                        struct_relation_map.setdefault((struct_name, struct_start_line, struct_end_line), []).append(trait_name)
                    # 添加impl中的函数
                    if impl_functions:
                        # print(f"Adding functions {impl_functions} to struct {struct_name}")
                        if struct_name not in impls:
                            impls[struct_name] = []
                        impls[struct_name].extend(impl_functions)
                        # print(f"Current impls for {struct_name}: {impls[struct_name]}")
                else:
                    pass
                    # print(f"No struct name found for impl block in file: {file_path}{node.start_point}")
            # 递归子节点
            for child in node.children:
                traverse(child)

        traverse(root_node)
        return structs, impls, functions, struct_relation_map, traits

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

def get_class_signature(file_full_path: str, struct_name: str) -> str:
    """获取结构体签名。

    Args:
        file_path (str): 文件路径。
        struct_name (str): 结构体名称。
    """
    rust_parser = RustParser()
    structs, _, _, _, _= rust_parser.extract_structs_and_functions(file_full_path)

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
