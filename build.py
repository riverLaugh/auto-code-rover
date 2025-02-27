from tree_sitter import Language, Parser

# 编译 tree-sitter Rust 语言解析库
Language.build_library(
    'build/my-languages.so',
    [
        'vendor/tree-sitter-rust'  # 替换为实际的 tree-sitter-rust 路径
    ]
)
