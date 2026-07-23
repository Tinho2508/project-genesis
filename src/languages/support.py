"""Suporte a multiplas linguagens de programacao."""

from dataclasses import dataclass, field


@dataclass
class Language:
    """Configuracao de uma linguagem de programacao."""

    name: str
    extension: str
    template: str
    keywords: list[str]
    example_prompt_prefix: str = "Escreva"
    comment_syntax: str = "#"
    supports_execution: bool = False

    def format_prompt(self, prompt: str) -> str:
        """Formata um prompt para esta linguagem."""
        return f"{self.example_prompt_prefix} em {self.name}: {prompt}"


# Linguagens suportadas
LANGUAGES: dict[str, Language] = {
    "python": Language(
        name="Python",
        extension=".py",
        template='def minha_funcao():\n    """Docstring."""\n    pass\n',
        keywords=["def", "class", "import", "return", "if", "else", "for", "while", "try", "except"],
        example_prompt_prefix="Escreva",
        comment_syntax="#",
        supports_execution=True,
    ),
    "javascript": Language(
        name="JavaScript",
        extension=".js",
        template="function minhaFuncao() {\n  // implementation\n}\n",
        keywords=["function", "const", "let", "var", "return", "if", "else", "for", "while", "class"],
        example_prompt_prefix="Escreva",
        comment_syntax="//",
        supports_execution=True,
    ),
    "typescript": Language(
        name="TypeScript",
        extension=".ts",
        template="function minhaFuncao(): void {\n  // implementation\n}\n",
        keywords=["function", "const", "let", "return", "if", "else", "for", "while", "interface", "type"],
        example_prompt_prefix="Escreva",
        comment_syntax="//",
        supports_execution=False,
    ),
    "java": Language(
        name="Java",
        extension=".java",
        template='public class Main {\n    public static void main(String[] args) {\n        // implementation\n    }\n}\n',
        keywords=["public", "private", "class", "void", "return", "if", "else", "for", "while", "import"],
        example_prompt_prefix="Escreva",
        comment_syntax="//",
        supports_execution=False,
    ),
    "c": Language(
        name="C",
        extension=".c",
        template="#include <stdio.h>\n\nint main() {\n    return 0;\n}\n",
        keywords=["int", "char", "void", "return", "if", "else", "for", "while", "include", "define"],
        example_prompt_prefix="Escreva",
        comment_syntax="//",
        supports_execution=False,
    ),
    "cpp": Language(
        name="C++",
        extension=".cpp",
        template='#include <iostream>\n\nint main() {\n    return 0;\n}\n',
        keywords=["int", "char", "void", "return", "if", "else", "for", "while", "class", "include"],
        example_prompt_prefix="Escreva",
        comment_syntax="//",
        supports_execution=False,
    ),
    "go": Language(
        name="Go",
        extension=".go",
        template='package main\n\nfunc main() {\n    // implementation\n}\n',
        keywords=["func", "package", "import", "return", "if", "else", "for", "range", "struct", "interface"],
        example_prompt_prefix="Escreva",
        comment_syntax="//",
        supports_execution=False,
    ),
    "rust": Language(
        name="Rust",
        extension=".rs",
        template="fn main() {\n    // implementation\n}\n",
        keywords=["fn", "let", "mut", "return", "if", "else", "for", "while", "struct", "impl"],
        example_prompt_prefix="Escreva",
        comment_syntax="//",
        supports_execution=False,
    ),
    "ruby": Language(
        name="Ruby",
        extension=".rb",
        template="#!/usr/bin/env ruby\n\ndef minha_funcao\n  # implementation\nend\n",
        keywords=["def", "end", "class", "return", "if", "else", "for", "while", "require", "puts"],
        example_prompt_prefix="Escreva",
        comment_syntax="#",
        supports_execution=False,
    ),
    "php": Language(
        name="PHP",
        extension=".php",
        template="<?php\n\nfunction minhaFuncao() {\n    // implementation\n}\n",
        keywords=["function", "class", "return", "if", "else", "for", "while", "echo", "array"],
        example_prompt_prefix="Escreva",
        comment_syntax="//",
        supports_execution=False,
    ),
}


class LanguageManager:
    """Gerencia linguagens suportadas."""

    def __init__(self):
        self.languages = LANGUAGES

    def get(self, name: str) -> Language | None:
        """Retorna uma linguagem pelo nome."""
        return self.languages.get(name.lower())

    def list_names(self) -> list[str]:
        """Retorna nomes de todas as linguagens suportadas."""
        return list(self.languages.keys())

    def list_supported(self) -> list[Language]:
        """Retorna todas as linguagens suportadas."""
        return list(self.languages.values())

    def get_execution_languages(self) -> list[str]:
        """Retorna linguagens que suportam execucao direta."""
        return [name for name, lang in self.languages.items() if lang.supports_execution]

    def get_extension_map(self) -> dict[str, str]:
        """Retorna mapeamento de linguagem -> extensao."""
        return {name: lang.extension for name, lang in self.languages.items()}

    def format_prompt_for(self, prompt: str, language: str) -> str:
        """Formata um prompt para uma linguagem especifica."""
        lang = self.get(language)
        if lang:
            return lang.format_prompt(prompt)
        return prompt
