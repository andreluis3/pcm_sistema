"""
pcm_repository.py
═════════════════
Persistência de resultados do experimento PCM.

Responsabilidade única: salvar e recuperar PCMResult.
Implementação simples em memória — substitua por SQLite/JSON se necessário.
"""
from __future__ import annotations

from .pcm_model import PCMResult


class PCMRepository:
    """
    Repositório em memória para resultados PCM.

    Mantém o último resultado processado para acesso posterior.
    Substituível por implementação com persistência em disco.
    """

    def __init__(self) -> None:
        self._last_result: PCMResult | None = None
        self._history: list[PCMResult] = []

    def save(self, result: PCMResult) -> None:
        """Salva um resultado processado."""
        self._last_result = result
        self._history.append(result)

    def get_last(self) -> PCMResult | None:
        """Retorna o último resultado salvo."""
        return self._last_result

    def get_history(self) -> list[PCMResult]:
        """Retorna todos os resultados salvos nesta sessão."""
        return list(self._history)

    def clear(self) -> None:
        """Limpa o histórico em memória."""
        self._last_result = None
        self._history.clear()