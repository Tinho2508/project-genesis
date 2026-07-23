"""Testes unitarios para o modulo de inferencia."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Testa se todos os modulos podem ser importados."""
    from src.model.config import ModelConfig, TrainingConfig
    from src.data.preprocessor import DataPreprocessor, CodeDataset
    from src.evaluation.evaluator import CodeEvaluator, EvaluationResult
    from src.executor.runner import CodeRunner, ExecutionResult
    from src.history.manager import HistoryManager
    from src.languages.support import LanguageManager

    print("OK: Todos os modulos importados com sucesso")


def test_model_config():
    """Testa as configuracoes do modelo."""
    from src.model.config import ModelConfig, TrainingConfig

    config = ModelConfig()
    assert config.model_name == "microsoft/CodeGPT-small-py"
    assert config.max_length == 512
    assert config.temperature == 0.7

    train_config = TrainingConfig()
    assert train_config.num_epochs == 3
    assert train_config.batch_size == 8
    assert Path(train_config.output_dir).exists()
    assert Path(train_config.log_dir).exists()

    print("OK: ModelConfig e TrainingConfig funcionais")


def test_preprocessor():
    """Testa o preprocessor de dados."""
    from src.data.preprocessor import DataPreprocessor

    preprocessor = DataPreprocessor()

    # Dataset de demonstracao
    prompts, codes = preprocessor.get_demo_dataset()
    assert len(prompts) > 0
    assert len(codes) > 0
    assert len(prompts) == len(codes)

    # Dataset amostral
    sample_prompts, sample_codes = preprocessor.create_sample_dataset(20)
    assert len(sample_prompts) == 20
    assert len(sample_codes) == 20

    print("OK: DataPreprocessor funcionando")


def test_evaluator():
    """Testa o avaliador de codigo."""
    from src.evaluation.evaluator import CodeEvaluator

    evaluator = CodeEvaluator()

    # Codigo valido
    result = evaluator.evaluate("def fatorial(n):\n    if n <= 1:\n        return 1\n    return n * fatorial(n-1)")
    assert result.is_valid_syntax is True
    assert result.score > 0
    assert result.status in ("APROVADO", "SINTAXE_OK")

    # Codigo com erro de sintaxe
    result = evaluator.evaluate("def foo(:\n    pass")
    assert result.is_valid_syntax is False
    assert result.status == "ERRO"

    print("OK: CodeEvaluator funcionando")


def test_runner():
    """Testa o executor de codigo."""
    from src.executor.runner import CodeRunner

    runner = CodeRunner(timeout_seconds=5)

    # Codigo Python valido
    result = runner.run("print(2 + 2)", "python")
    assert result.success is True
    assert result.output == "4"

    # Codigo com erro
    result = runner.run("print(1/0)", "python")
    assert result.success is False

    print("OK: CodeRunner funcionando")


def test_history():
    """Testa o gerenciamento de historico."""
    import tempfile
    from src.history.manager import HistoryManager

    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = str(Path(tmpdir) / "test_history.json")
        manager = HistoryManager(history_file)

        # Adicionar entradas
        entry1 = manager.add(prompt="Teste 1", code="print(1)", language="python")
        entry2 = manager.add(prompt="Teste 2", code="print(2)", language="python")
        assert len(manager.entries) == 2

        # Buscar
        found = manager.get(entry1.id)
        assert found is not None
        assert found.prompt == "Teste 1"

        # Favorito
        manager.toggle_favorite(entry1.id)
        assert len(manager.get_favorites()) == 1

        # Busca
        results = manager.search("Teste 2")
        assert len(results) == 1

        # Undo (desfaz toggle_favorite, volta ao estado anterior)
        manager.undo()
        assert len(manager.entries) == 2

        # Redo (refaz toggle_favorite)
        manager.redo()
        assert len(manager.entries) == 2

        # Deletar
        manager.delete(entry1.id)
        assert len(manager.entries) == 1

        # Stats
        stats = manager.stats()
        assert stats["total"] == 1

    print("OK: HistoryManager funcionando")


def test_language_manager():
    """Testa o gerenciador de linguagens."""
    from src.languages.support import LanguageManager

    manager = LanguageManager()

    # Listar linguagens
    names = manager.list_names()
    assert "python" in names
    assert "javascript" in names
    assert len(names) >= 8

    # Buscar linguagem
    py = manager.get("python")
    assert py is not None
    assert py.name == "Python"
    assert py.extension == ".py"

    # Linguagens com execucao
    exec_langs = manager.get_execution_languages()
    assert "python" in exec_langs

    # Formatar prompt
    prompt = manager.format_prompt_for("calcule fatorial", "python")
    assert "Python" in prompt

    print("OK: LanguageManager funcionando")


if __name__ == "__main__":
    print("=" * 50)
    print("  TESTES UNITARIOS - PROJECT GENESIS")
    print("=" * 50)
    print()

    tests = [
        test_imports,
        test_model_config,
        test_preprocessor,
        test_evaluator,
        test_runner,
        test_history,
        test_language_manager,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"FALHOU: {test.__name__} - {e}")
            failed += 1

    print()
    print(f"Resultado: {passed} passed, {failed} failed de {len(tests)} testes")
    print("=" * 50)
