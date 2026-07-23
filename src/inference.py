"""Project Genesis - Gerador de Codigo com Inteligencia Artificial.

Uso:
    python src/inference.py "Escreva uma funcao que calcule o fatorial"
    python src/inference.py --interactive
    python src/inference.py --model outputs/models/final "Crie um palindromo"
"""

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """### Instrucao:
{prompt}

### Codigo:
"""


class CodeGenerator:
    """Gerador de codigo usando modelos de linguagem."""

    def __init__(self, model_name: str = "microsoft/CodeGPT-small-py", device: str = None):
        import torch

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_name = model_name
        self.model = None
        self.tokenizer = None

    def load_model(self, model_path: str = None):
        """Carrega o modelo e o tokenizer."""
        from transformers import AutoModelForCausalLM, AutoTokenizer

        path = model_path or self.model_name
        logger.info(f"Carregando modelo de: {path}")

        self.tokenizer = AutoTokenizer.from_pretrained(path)
        self.model = AutoModelForCausalLM.from_pretrained(path)
        self.model.to(self.device)
        self.model.eval()

        logger.info(f"Modelo carregado em {self.device}")

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.95,
        repetition_penalty: float = 1.2,
    ) -> str:
        """Gera codigo a partir de uma instrucao em linguagem natural."""
        import torch

        if self.model is None:
            self.load_model()

        full_prompt = PROMPT_TEMPLATE.format(prompt=prompt)
        inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                repetition_penalty=repetition_penalty,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        generated = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        if "### Codigo:" in generated:
            code = generated.split("### Codigo:")[-1].strip()
        else:
            code = generated[len(full_prompt):].strip()

        return code

    def generate_batch(self, prompts: list[str], **kwargs) -> list[str]:
        """Gera codigo para multiplos prompts."""
        return [self.generate(p, **kwargs) for p in prompts]


def criar_parser() -> argparse.ArgumentParser:
    """Cria o parser de argumentos da CLI."""
    parser = argparse.ArgumentParser(
        description="Project Genesis - Gerador de Codigo com IA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python src/inference.py "Escreva uma funcao que calcule fatorial"
  python src/inference.py --interactive
  python src/inference.py --model outputs/models/final --temp 0.8 "Crie um palindromo"
        """,
    )

    parser.add_argument(
        "prompt",
        nargs="?",
        help="Instrucao em linguagem natural para gerar codigo",
    )
    parser.add_argument(
        "--model", "-m",
        default=None,
        help="Caminho para o modelo treinado (default: modelo base)",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Modo interativo (loop de perguntas)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=256,
        help="Numero maximo de tokens a gerar (default: 256)",
    )
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.7,
        help="Temperatura para sampling (default: 0.7)",
    )

    return parser


def modo_interativo(generator: CodeGenerator, args) -> None:
    """Executa o modo interativo de geracao de codigo."""
    print("\n" + "=" * 60)
    print("  PROJECT GENESIS - Gerador de Codigo com IA")
    print("  Modo Interativo")
    print("  Digite 'sair' ou 'quit' para encerrar")
    print("=" * 60 + "\n")

    while True:
        try:
            prompt = input("Instrucao > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSaindo...")
            break

        if not prompt:
            continue
        if prompt.lower() in ("sair", "quit", "exit"):
            print("Ate logo!")
            break

        print("\nGerando codigo...")
        try:
            code = generator.generate(
                prompt,
                max_new_tokens=args.max_tokens,
                temperature=args.temperature,
            )
            print("\n--- Codigo Gerado ---")
            print(code)
            print("--- Fim ---\n")
        except Exception as e:
            print(f"Erro ao gerar codigo: {e}\n")


def main() -> None:
    """Ponto de entrada principal."""
    parser = criar_parser()
    args = parser.parse_args()

    generator = CodeGenerator(model_name="microsoft/CodeGPT-small-py")
    generator.load_model(model_path=args.model)

    if args.interactive:
        modo_interativo(generator, args)
    elif args.prompt:
        print("\nGerando codigo...")
        code = generator.generate(
            args.prompt,
            max_new_tokens=args.max_tokens,
            temperature=args.temperature,
        )
        print("\n--- Codigo Gerado ---")
        print(code)
        print("--- Fim ---")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
