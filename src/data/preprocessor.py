"""Processamento de dados para treinamento de modelos de geracao de codigo."""

import json
import logging
from pathlib import Path
from typing import Optional

import torch
from torch.utils.data import Dataset

logger = logging.getLogger(__name__)


# Dados de exemplo para demonstracao
EXAMPLE_PROMPTS = [
    "Escreva uma funcao Python que calcule o fatorial de um numero",
    "Crie uma funcao que verifique se uma string e um palindromo",
    "Implemente uma funcao que retorne os N primeiros numeros de Fibonacci",
    "Escreva uma funcao que ordene uma lista de inteiros usando bubble sort",
    "Crie uma funcao que conte as vogais de uma string",
    "Implemente uma funcao que encontre o maior elemento em uma lista",
    "Escreva uma funcao que converta Celsius para Fahrenheit",
    "Crie uma funcao que verifique se um numero e primo",
    "Implemente uma funcao que remova duplicatas de uma lista",
    "Escreva uma funcao que calcule a media de uma lista de numeros",
]

EXAMPLE_CODES = [
    "def fatorial(n):\n    if n <= 1:\n        return 1\n    return n * fatorial(n - 1)",
    "def eh_palindromo(s):\n    s = s.lower().replace(' ', '')\n    return s == s[::-1]",
    "def fibonacci(n):\n    fib = [0, 1]\n    for i in range(2, n):\n        fib.append(fib[i-1] + fib[i-2])\n    return fib[:n]",
    "def bubble_sort(lista):\n    n = len(lista)\n    for i in range(n):\n        for j in range(0, n-i-1):\n            if lista[j] > lista[j+1]:\n                lista[j], lista[j+1] = lista[j+1], lista[j]\n    return lista",
    "def contar_vogais(s):\n    vogais = 'aeiou'\n    return sum(1 for c in s.lower() if c in vogais)",
    "def maior_elemento(lista):\n    if not lista:\n        return None\n    return max(lista)",
    "def celsius_para_fahrenheit(c):\n    return (c * 9/5) + 32",
    "def eh_primo(n):\n    if n < 2:\n        return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0:\n            return False\n    return True",
    "def remover_duplicatas(lista):\n    return list(dict.fromkeys(lista))",
    "def media_lista(numeros):\n    if not numeros:\n        return 0\n    return sum(numeros) / len(numeros)",
]


class CodeDataset(Dataset):
    """Dataset de pares prompt-codigo para treinamento."""

    def __init__(self, prompts: list[str], codes: list[str], tokenizer, max_length: int = 512):
        self.prompts = prompts
        self.codes = codes
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.prompts)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        prompt = self.prompts[idx]
        code = self.codes[idx]

        input_text = f"### Instrucao:\n{prompt}\n\n### Codigo:\n"
        target_text = f"{code}{self.tokenizer.eos_token}"

        full_text = input_text + target_text

        encoding = self.tokenizer(
            full_text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        labels = encoding["input_ids"].clone()
        prompt_encoding = self.tokenizer(
            input_text,
            max_length=self.max_length,
            truncation=True,
            return_tensors="pt",
        )
        prompt_len = prompt_encoding["input_ids"].shape[1]
        labels[0, :prompt_len] = -100

        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": labels.squeeze(),
        }


class DataPreprocessor:
    """Preprocessador de dados para treinamento."""

    def __init__(self, cache_dir: str = "data"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def load_custom_dataset(self, file_path: str) -> tuple[list[str], list[str]]:
        """Carrega um dataset personalizado de um arquivo JSON.

        Formato esperado:
        [
            {"prompt": "...", "code": "..."},
            ...
        ]
        """
        data = json.loads(Path(file_path).read_text(encoding="utf-8"))
        prompts = [item["prompt"] for item in data]
        codes = [item["code"] for item in data]
        logger.info(f"Carregados {len(prompts)} exemplos de {file_path}")
        return prompts, codes

    def save_dataset(self, prompts: list[str], codes: list[str], file_path: str) -> None:
        """Salva um dataset em formato JSON."""
        data = [{"prompt": p, "code": c} for p, c in zip(prompts, codes)]
        Path(file_path).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info(f"Dataset salvo em {file_path} ({len(data)} exemplos)")

    def get_demo_dataset(self) -> tuple[list[str], list[str]]:
        """Retorna o dataset de demonstracao."""
        return EXAMPLE_PROMPTS, EXAMPLE_CODES

    def create_sample_dataset(self, num_samples: int = 100) -> tuple[list[str], list[str]]:
        """Cria um dataset de demonstracao repetindo exemplos com variacoes."""
        prompts = []
        codes = []

        import random
        random.seed(42)

        prefixos = ["Escreva", "Crie", "Implemente", "Desenvolva", "Gere"]
        sufixos = [
            "em Python", "usando Python", "em Python 3",
            "de forma eficiente", "com tratamento de erros",
        ]

        while len(prompts) < num_samples:
            idx = len(prompts) % len(EXAMPLE_PROMPTS)
            prefix = random.choice(prefixos)
            suffix = random.choice(sufixos)

            base_prompt = EXAMPLE_PROMPTS[idx]
            words = base_prompt.split()
            action = words[0] if words else "Escreva"
            rest = " ".join(words[1:])

            new_prompt = f"{prefix} {rest} {suffix}"
            prompts.append(new_prompt)
            codes.append(EXAMPLE_CODES[idx])

        return prompts[:num_samples], codes[:num_samples]
