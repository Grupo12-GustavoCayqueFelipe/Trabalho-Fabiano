"""
Gate para OWASP ZAP: retorna 1 se houver alertas HIGH ou relatório inválido.

ZAP trabalha com riscos Informational, Low, Medium e High (3). Assim,
HIGH é o nível bloqueante mais alto disponível nesse scanner.
"""

import json
import sys
from pathlib import Path


def verificar_relatorio(caminho: Path) -> list[dict]:
    if not caminho.is_file():
        raise ValueError(f'Relatório ZAP não gerado: {caminho}')
    try:
        dados = json.loads(caminho.read_text(encoding='utf-8'))
    except (OSError, ValueError) as erro:
        raise ValueError(f'Relatório ZAP ilegível: {erro}') from erro
    if not isinstance(dados, dict) or not isinstance(dados.get('site'), list):
        raise ValueError('Relatório ZAP fora do formato esperado (site[])')

    altos = []
    for site in dados['site']:
        if not isinstance(site, dict):
            raise ValueError('Entrada inválida no relatório ZAP')
        alertas = site.get('alerts', [])
        if not isinstance(alertas, list):
            raise ValueError('Campo alerts não é lista')
        for alerta in alertas:
            nivel = str(alerta.get('riskcode', '')).strip()
            rotulo = str(alerta.get('riskdesc', '')).strip().lower()
            if nivel == '3' or rotulo.startswith('high'):
                altos.append({
                    'pluginid': alerta.get('pluginid', 'desconhecido'),
                    'nome': alerta.get('name') or alerta.get('alert', 'sem nome'),
                    'instancias': len(alerta.get('instances', [])),
                })
    return altos


def main() -> int:
    if len(sys.argv) != 2:
        print('Uso: python zap_gate.py caminho/zap.json', file=sys.stderr)
        return 2
    try:
        altos = verificar_relatorio(Path(sys.argv[1]))
    except ValueError as erro:
        print(f'FALHA de infraestrutura/relatório: {erro}', file=sys.stderr)
        return 1
    if altos:
        print(f'BLOQUEADO: {len(altos)} alerta(s) de risco ALTO encontrados pelo ZAP')
        for item in altos:
            print(f"- {item['pluginid']}: {item['nome']} ({item['instancias']} ocorrência(s))")
        return 1
    print('APROVADO: nenhuma vulnerabilidade de risco ALTO no relatório ZAP.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
