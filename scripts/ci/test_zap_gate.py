"""Testes unitários do bloqueio de alertas do OWASP ZAP. Não requer Django."""

import json
import tempfile
import unittest
from pathlib import Path

from zap_gate import verificar_relatorio


class TestZapGate(unittest.TestCase):
    def escrever(self, payload):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        p = Path(tmp.name) / 'zap.json'
        p.write_text(json.dumps(payload), encoding='utf-8')
        return p

    def test_alto_bloqueia(self):
        p = self.escrever({'site': [{'alerts': [{'riskcode': '3', 'name': 'SQL injection'}]}]})
        self.assertEqual(len(verificar_relatorio(p)), 1)

    def test_medio_nao_bloqueia(self):
        p = self.escrever({'site': [{'alerts': [{'riskcode': '2', 'name': 'Header'}]}]})
        self.assertEqual(verificar_relatorio(p), [])

    def test_sem_site_falha_fechada(self):
        p = self.escrever({'alerts': []})
        with self.assertRaises(ValueError):
            verificar_relatorio(p)


if __name__ == '__main__':
    unittest.main()
