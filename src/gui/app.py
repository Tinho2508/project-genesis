"""Interface grafica do Project Genesis."""

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import customtkinter as ctk

    HAS_GUI = True
except ImportError:
    HAS_GUI = False


class GenesisApp:
    """Interface grafica principal."""

    def __init__(self):
        if not HAS_GUI:
            raise ImportError("customtkinter nao esta instalado. Execute: pip install customtkinter")

        self.generator = None
        self.evaluator = None
        self.history = None
        self.lang_manager = None

        self._setup_window()

    def _setup_window(self):
        """Configura a janela principal."""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.window = ctk.CTk()
        self.window.geometry("900x700")
        self.window.title("Project Genesis - Gerador de Codigo com IA")

        # Header
        header = ctk.CTkFrame(self.window, height=60)
        header.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            header,
            text="PROJECT GENESIS",
            font=("Arial", 24, "bold"),
            text_color="#4CAF50",
        ).pack(side="left", padx=20, pady=10)

        # Language selector
        self.lang_var = ctk.StringVar(value="python")
        self.lang_menu = ctk.CTkOptionMenu(
            header,
            values=["python", "javascript", "typescript", "java", "c", "cpp", "go", "rust", "ruby", "php"],
            variable=self.lang_var,
            width=150,
        )
        self.lang_menu.pack(side="right", padx=20, pady=10)

        ctk.CTkLabel(header, text="Linguagem:", font=("Arial", 12)).pack(side="right", padx=(0, 5))

        # Main content area
        content = ctk.CTkFrame(self.window)
        content.pack(fill="both", expand=True, padx=10, pady=5)

        # Left panel - Input
        left_panel = ctk.CTkFrame(content, width=400)
        left_panel.pack(side="left", fill="both", expand=True, padx=(5, 2), pady=5)

        ctk.CTkLabel(
            left_panel, text="INSTRUCAO", font=("Arial", 14, "bold")
        ).pack(pady=(10, 5))

        self.prompt_entry = ctk.CTkTextbox(left_panel, height=120, font=("Arial", 13))
        self.prompt_entry.pack(fill="x", padx=10, pady=5)
        self.prompt_entry.insert("1.0", "Escreva uma funcao que calcule o fatorial de um numero")

        # Buttons frame
        btn_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)

        self.btn_generate = ctk.CTkButton(
            btn_frame,
            text="GERAR CODIGO",
            command=self._on_generate,
            fg_color="#4CAF50",
            hover_color="#388E3C",
            font=("Arial", 14, "bold"),
            height=40,
        )
        self.btn_generate.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.btn_execute = ctk.CTkButton(
            btn_frame,
            text="EXECUTAR",
            command=self._on_execute,
            fg_color="#2196F3",
            hover_color="#1976D2",
            font=("Arial", 14, "bold"),
            height=40,
        )
        self.btn_execute.pack(side="right", expand=True, fill="x", padx=(5, 0))

        # Options
        opt_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        opt_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(opt_frame, text="Temperature:").pack(side="left")
        self.temp_slider = ctk.CTkSlider(opt_frame, from_=0.1, to=2.0, number_of_points=19)
        self.temp_slider.set(0.7)
        self.temp_slider.pack(side="left", padx=5)

        ctk.CTkLabel(opt_frame, text="Max Tokens:").pack(side="left", padx=(20, 0))
        self.max_tokens_entry = ctk.CTkEntry(opt_frame, width=60)
        self.max_tokens_entry.insert(0, "256")
        self.max_tokens_entry.pack(side="left", padx=5)

        # Right panel - Output
        right_panel = ctk.CTkFrame(content, width=400)
        right_panel.pack(side="right", fill="both", expand=True, padx=(2, 5), pady=5)

        ctk.CTkLabel(
            right_panel, text="CODIGO GERADO", font=("Arial", 14, "bold")
        ).pack(pady=(10, 5))

        self.code_output = ctk.CTkTextbox(right_panel, font=("Consolas", 13))
        self.code_output.pack(fill="both", expand=True, padx=10, pady=5)

        # Score label
        self.score_label = ctk.CTkLabel(
            right_panel, text="Score: --", font=("Arial", 12)
        )
        self.score_label.pack(pady=(0, 5))

        # Bottom panel - Execution output
        bottom = ctk.CTkFrame(self.window, height=150)
        bottom.pack(fill="x", padx=10, pady=(5, 10))

        ctk.CTkLabel(
            bottom, text="SAIDA DA EXECUCAO", font=("Arial", 12, "bold")
        ).pack(pady=(5, 0))

        self.exec_output = ctk.CTkTextbox(bottom, font=("Consolas", 11), height=80)
        self.exec_output.pack(fill="x", padx=10, pady=5)

        # Status bar
        self.status_label = ctk.CTkLabel(
            self.window, text="Pronto", font=("Arial", 10), text_color="gray"
        )
        self.status_label.pack(pady=(0, 5))

    def _load_dependencies(self):
        """Carrega as dependencias sob demanda."""
        if self.generator is None:
            from src.inference import CodeGenerator
            self.generator = CodeGenerator()
            self.generator.load_model()

        if self.evaluator is None:
            from src.evaluation.evaluator import CodeEvaluator
            self.evaluator = CodeEvaluator()

        if self.history is None:
            from src.history.manager import HistoryManager
            self.history = HistoryManager()

        if self.lang_manager is None:
            from src.languages.support import LanguageManager
            self.lang_manager = LanguageManager()

    def _on_generate(self):
        """Handler do botao Gerar."""
        self.btn_generate.configure(state="disabled", text="GERANDO...")
        self.status_label.configure(text="Gerando codigo...", text_color="orange")
        self.window.update()

        threading.Thread(target=self._generate_thread, daemon=True).start()

    def _generate_thread(self):
        """Thread de geracao de codigo."""
        try:
            self._load_dependencies()

            prompt = self.prompt_entry.get("1.0", "end").strip()
            language = self.lang_var.get()
            temperature = self.temp_slider.get()
            max_tokens = int(self.max_tokens_entry.get() or "256")

            if not prompt:
                self._show_error("Digite uma instrucao primeiro.")
                return

            # Gerar codigo
            code = self.generator.generate(
                prompt=prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
            )

            # Avaliar
            eval_result = self.evaluator.evaluate(code, language)

            # Atualizar interface
            self.code_output.delete("1.0", "end")
            self.code_output.insert("1.0", code)

            self.score_label.configure(
                text=f"Score: {eval_result.score}/10 | Status: {eval_result.status}"
            )

            # Salvar no historico
            self.history.add(
                prompt=prompt,
                code=code,
                language=language,
                score=eval_result.score,
            )

            self.status_label.configure(text="Codigo gerado com sucesso!", text_color="green")

        except Exception as e:
            self._show_error(str(e))
        finally:
            self.btn_generate.configure(state="normal", text="GERAR CODIGO")

    def _on_execute(self):
        """Handler do botao Executar."""
        code = self.code_output.get("1.0", "end").strip()
        if not code:
            self._show_error("Nenhum codigo para executar.")
            return

        self.btn_execute.configure(state="disabled", text="EXECUTANDO...")
        self.status_label.configure(text="Executando codigo...", text_color="orange")
        self.window.update()

        threading.Thread(target=self._execute_thread, args=(code,), daemon=True).start()

    def _execute_thread(self, code: str):
        """Thread de execucao de codigo."""
        try:
            from src.executor.runner import CodeRunner
            runner = CodeRunner()

            language = self.lang_var.get()
            result = runner.run(code, language)

            self.exec_output.delete("1.0", "end")
            if result.output:
                self.exec_output.insert("1.0", f"Saida:\n{result.output}")
            if result.error:
                self.exec_output.insert("end", f"\n\nErros:\n{result.error}")

            status = "Executado" if result.success else "Erro na execucao"
            color = "green" if result.success else "red"
            self.status_label.configure(
                text=f"{status} ({result.execution_time_ms:.0f}ms)", text_color=color
            )

        except Exception as e:
            self._show_error(str(e))
        finally:
            self.btn_execute.configure(state="normal", text="EXECUTAR")

    def _show_error(self, message: str):
        """Exibe mensagem de erro."""
        self.status_label.configure(text=f"Erro: {message}", text_color="red")

    def run(self):
        """Inicia a aplicacao."""
        self.window.mainloop()


def main():
    """Ponto de entrada da GUI."""
    app = GenesisApp()
    app.run()


if __name__ == "__main__":
    main()
