extern crate pyo3;
extern crate serde;
extern crate serde_json;
extern crate syn;

use pyo3::prelude::*;
use quote::ToTokens;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::ops::Deref;
use syn::spanned::Spanned;
use syn::{FnArg, ImplItem, Item, ReturnType};

// Rust 解析的数据结构
// 定义 RustSourceMethod
#[derive(Debug, Serialize, Deserialize, Clone)]
struct RustSourceMethod {
    name: String,
    start_line: usize,
    end_line: usize,
}

// 定义 RustSourceStruct
#[derive(Debug, Serialize, Deserialize, Clone)]
struct RustSourceStruct {
    name: String,
    methods: Vec<RustSourceMethod>,
    start_line: usize,
    end_line: usize,
}

// 定义 RustSourceFunction
#[derive(Debug, Serialize, Deserialize, Clone)]
struct RustSourceFunction {
    name: String,
    start_line: usize,
    end_line: usize,
}

// 定义 RustSourceVariable
#[derive(Debug, Serialize, Deserialize, Clone)]
struct RustSourceVariable {
    name: String,
    start_line: usize,
    end_line: usize,
}

// 定义 RustFileResult
#[derive(Debug, Serialize, Deserialize, Clone)]
struct RustSourceFile {
    structs: Vec<RustSourceStruct>,
    functions: Vec<RustSourceFunction>,
    variables: Vec<RustSourceVariable>,
    lines: Vec<String>,
}

// 解析 Rust 代码的函数
#[pyfunction]
fn parse_rust_code(code: &str) -> PyResult<String> {

    let lines: Vec<String> = code.lines().map(|s| s.to_string()).collect();

    match syn::parse_file(code) {
        Ok(ast) => {
            // 从根开始，递归地处理文件内容
            let (s, f, v) = parse_mod(&ast.items);

            let result = RustSourceFile {
                structs: s,
                functions: f,
                variables: v,
                lines,
            };

            // 返回 JSON 格式的结果
            Ok(serde_json::to_string(&result).unwrap())
        }
        Err(e) => Err(pyo3::exceptions::PySyntaxError::new_err(e.to_string())),
    }
}

fn parse_mod(
    items: &[Item],
) -> (
    Vec<RustSourceStruct>,
    Vec<RustSourceFunction>,
    Vec<RustSourceVariable>,
)
{
    let mut structs = Vec::new();
    let mut functions = Vec::new();
    let mut variables = Vec::new();

    // 存储 struct 和 impl 之间的关系
    let mut struct_map: HashMap<String, Vec<RustSourceMethod>> = HashMap::new();

    // 遍历 AST 的每个条目
    for item in items {
        match item {
            // 解析 struct
            Item::Struct(s) => {
                let struct_name = s.ident.to_string();

                struct_map.insert(struct_name.clone(), Vec::new());

                let start_line = s.span().start().line;
                let end_line = s.span().end().line;

                structs.push(RustSourceStruct {
                    name: struct_name,
                    methods: Vec::new(),
                    start_line,
                    end_line,
                });
            }

            // 解析 impl 块
            Item::Impl(imp) => {
                if let syn::Type::Path(type_path) = imp.self_ty.deref() {
                    let struct_name = type_path.path.segments[0].ident.to_string();
                    if let Some(impls) = struct_map.get_mut(&struct_name) {
                        for item in &imp.items {
                            if let ImplItem::Fn(i) = item {
                                let start_line = i.span().start().line;
                                let end_line = i.span().end().line;
                                impls.push(RustSourceMethod {
                                    name: i.sig.ident.to_string(),
                                    start_line,
                                    end_line,
                                });
                            }
                        }
                    }
                }
            }

            // 解析独立的函数
            Item::Fn(f) => {
                let start_line = f.span().start().line;
                let end_line = f.span().end().line;
                functions.push(RustSourceFunction {
                    name: f.sig.ident.to_string(),
                    start_line,
                    end_line,
                });
            }

            // 解析全局静态变量
            Item::Static(s) => {
                let start_line = s.span().start().line;
                let end_line = s.span().end().line;
                variables.push(RustSourceVariable {
                    name: s.ident.to_string(),
                    start_line,
                    end_line,
                })
            }

            // 解析全局常量
            Item::Const(c) => {
                let start_line = c.span().start().line;
                let end_line = c.span().end().line;
                variables.push(RustSourceVariable {
                    name: c.ident.to_string(),
                    start_line,
                    end_line,
                })
            }

            Item::Mod(m) => {
                // 获取模块内的项，这里需要解包 Option
                if let Some((_, ref nested_items)) = &m.content {
                    let (mut s, mut f, mut v) = parse_mod(nested_items);
                    structs.append(&mut s);
                    functions.append(&mut f);
                    variables.append(&mut v);
                }
            }

            _ => {}
        }
    }

    // 将方法归属于相应的 struct
    for struct_item in &mut structs {
        if let Some(methods) = struct_map.remove(&struct_item.name) {
            struct_item.methods = methods;
        }
    }

    (structs, functions, variables)
}

// 压缩 Rust 代码的函数
#[pyfunction]
fn compress_rust_code(code: &str) -> PyResult<String> {
    match syn::parse_file(code) {
        Ok(ast) => {
            // 从根开始，递归地处理文件内容
            Ok(compress_mod(&ast.items, 0))
        }
        Err(e) => Err(pyo3::exceptions::PySyntaxError::new_err(e.to_string())),
    }
}

// 递归处理 mod 和其他代码块
fn compress_mod(items: &[Item], depth: usize) -> String {
    let mut result = String::new();

    let indent = " ".repeat(depth * 4); // 根据 ident 计算缩进量，4个空格一层

    for item in items {
        match item {
            // 处理结构体
            Item::Struct(s) => {
                result.push_str(&format!("{}struct {} {{ ... }}\n", indent, s.ident));
            }

            // 处理枚举
            Item::Enum(e) => {
                result.push_str(&format!("{}enum {} {{ ... }}\n", indent, e.ident));
            }

            // 处理函数
            Item::Fn(f) => {
                let signature = &f.sig;
                let ident = &signature.ident;

                // 获取函数参数
                let params = signature
                    .inputs
                    .iter()
                    .map(|arg| match arg {
                        FnArg::Typed(pat_type) => {
                            let param_name = &pat_type.pat;
                            let param_type = &pat_type.ty;
                            format!(
                                "{}: {}",
                                quote::quote! { #param_name },
                                quote::quote! { #param_type }
                            )
                        }
                        FnArg::Receiver(_) => "self".to_string(),
                    })
                    .collect::<Vec<String>>()
                    .join(", ");

                // 获取返回类型
                let return_type = match &signature.output {
                    ReturnType::Default => "".to_string(),
                    ReturnType::Type(_, ty) => format!(" -> {}", quote::quote! { #ty }),
                };

                result.push_str(&format!(
                    "{}fn {}({}){} {{ ... }}\n",
                    indent, ident, params, return_type
                ));
            }

            // 处理 impl 块
            Item::Impl(impl_block) => {
                let impl_type = &impl_block.self_ty;
                result.push_str(&format!(
                    "{}impl {} {{\n",
                    indent,
                    quote::quote! { #impl_type }
                ));

                // 递归处理 impl 内的函数
                for impl_item in &impl_block.items {
                    match impl_item {
                        ImplItem::Fn(method) => {
                            let signature = &method.sig;
                            let ident = &signature.ident;

                            // 获取方法参数
                            let params = signature
                                .inputs
                                .iter()
                                .map(|arg| match arg {
                                    FnArg::Typed(pat_type) => {
                                        let param_name = &pat_type.pat;
                                        let param_type = &pat_type.ty;
                                        format!(
                                            "{}: {}",
                                            quote::quote! { #param_name },
                                            quote::quote! { #param_type }
                                        )
                                    }
                                    FnArg::Receiver(_) => "self".to_string(),
                                })
                                .collect::<Vec<String>>()
                                .join(", ");

                            // 获取返回类型
                            let return_type = match &signature.output {
                                ReturnType::Default => "".to_string(),
                                ReturnType::Type(_, ty) => {
                                    format!(" -> {}", quote::quote! { #ty })
                                }
                            };

                            result.push_str(&format!(
                                "{}    fn {}({}){} {{ ... }}\n",
                                indent, ident, params, return_type
                            ));
                        }
                        _ => {}
                    }
                }

                result.push_str(&format!("{}}}\n", indent));
            }

            // 处理模块（递归）
            Item::Mod(m) => {
                // 获取模块内的项，这里需要解包 Option
                if let Some((_, ref nested_items)) = &m.content {
                    result.push_str(&format!("{}mod {} {{\n", indent, &m.ident));

                    // 递归调用处理模块内容
                    let nested_result = compress_mod(nested_items, depth + 1);
                    result.push_str(&nested_result);
                    result.push_str(&format!("{}}}\n", indent));
                }
            }

            // 处理宏
            Item::Macro(m) => match m.ident {
                Some(ref ident) => {
                    result.push_str(&format!("{}macro_rules! {} {{ ... }}\n", indent, ident));
                }
                None => {
                    result.push_str(&format!(
                        "{}{}! {{ ... }}\n",
                        indent,
                        m.mac.path.to_token_stream()
                    ));
                }
            },

            // 处理全局常量
            Item::Const(c) => {
                result.push_str(&format!(
                    "{}const {}: {} = ...;\n",
                    indent,
                    c.ident,
                    c.ty.to_token_stream()
                ));
            }

            // 处理静态变量
            Item::Static(s) => {
                let mutability = if matches!(s.mutability, syn::StaticMutability::Mut(_)) {
                    "mut "
                } else {
                    ""
                };
                result.push_str(&format!(
                    "{}static {}{}: {} = ...;\n",
                    indent,
                    mutability,
                    s.ident,
                    s.ty.to_token_stream()
                ));
            }

            // 忽略其他类型
            _ => {}
        }
    }

    result
}

// PyO3 的模块入口函数
#[pymodule]
fn parser(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse_rust_code, m)?)?;
    m.add_function(wrap_pyfunction!(compress_rust_code, m)?)?;
    Ok(())
}