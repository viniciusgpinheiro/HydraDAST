#!/usr/bin/env python3
"""
Script para Verificar e Sugerir Atualização de Dependências
Desenvolvido pela AulasHack para manter projetos atualizados

Uso:
    python check_dependencies.py
"""

import subprocess
import sys
import json
from datetime import datetime
from packaging import version

def print_header(text):
    """Imprime um cabeçalho formatado"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80 + "\n")

def check_python_version():
    """Verifica versão do Python"""
    print_header("🐍 VERIFICAÇÃO DE VERSÃO PYTHON")
    
    major, minor, micro = sys.version_info[:3]
    current_version = f"{major}.{minor}.{micro}"
    
    print(f"Versão Atual: Python {current_version}")
    
    # Versões suportadas
    supported = {
        '3.9': {'status': '✅ Mínima suportada', 'eol': 'Oct 2026'},
        '3.10': {'status': '✅ Suportada', 'eol': 'Oct 2026'},
        '3.11': {'status': '✅ Suportada', 'eol': 'Oct 2027'},
        '3.12': {'status': '✅ Recomendada', 'eol': 'Oct 2028'},
        '3.13': {'status': '✅ Nova', 'eol': 'Oct 2029'},
        '3.14': {'status': '⚠️ Beta', 'eol': 'Out 2026'},
    }
    
    base_version = f"{major}.{minor}"
    
    if base_version in supported:
        info = supported[base_version]
        print(f"Status: {info['status']}")
        print(f"Fim de Suporte: {info['eol']}")
    else:
        print(f"⚠️ Versão {base_version} pode não ser suportada")
    
    return major, minor

def check_installed_packages():
    """Lista pacotes instalados e suas versões"""
    print_header("📦 PACOTES INSTALADOS")
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'list', '--format=json'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            packages = json.loads(result.stdout)
            
            # Filtrar apenas pacotes do projeto
            important_packages = [
                'Flask', 'Flask-SQLAlchemy', 'SQLAlchemy', 'Werkzeug',
                'Jinja2', 'Click', 'MarkupSafe', 'itsdangerous'
            ]
            
            print("Principais pacotes instalados:\n")
            for pkg in packages:
                if pkg['name'] in important_packages or any(imp.lower() in pkg['name'].lower() for imp in important_packages):
                    print(f"  {pkg['name']:<25} {pkg['version']}")
            
            return packages
    except Exception as e:
        print(f"❌ Erro ao listar pacotes: {e}")
        return None

def check_outdated_packages():
    """Verifica pacotes desatualizados"""
    print_header("🔄 VERIFICAÇÃO DE ATUALIZAÇÕES")
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'list', '--outdated', '--format=json'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            outdated = json.loads(result.stdout)
            
            if outdated:
                print(f"Encontrados {len(outdated)} pacote(s) desatualizado(s):\n")
                for pkg in outdated:
                    print(f"  {pkg['name']:<25}")
                    print(f"    Versão Atual: {pkg['version']}")
                    print(f"    Versão Nova: {pkg['latest_version']}")
                    print()
                
                return outdated
            else:
                print("✅ Todos os pacotes estão atualizados!")
                return []
    except Exception as e:
        print(f"⚠️ Erro ao verificar atualizações: {e}")
        print("Tente: python -m pip install --upgrade pip")
        return None

def check_vulnerabilities():
    """Verifica vulnerabilidades de segurança"""
    print_header("🔐 VERIFICAÇÃO DE VULNERABILIDADES")
    
    try:
        # Tentar usar pip-audit
        result = subprocess.run(
            ['pip', 'audit'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if "No known security vulnerabilities found" in result.stdout:
            print("✅ Nenhuma vulnerabilidade conhecida encontrada!")
            return True
        else:
            print("⚠️ Vulnerabilidades encontradas:")
            print(result.stdout)
            return False
            
    except FileNotFoundError:
        print("⚠️ pip-audit não instalado")
        print("\nPara verificar vulnerabilidades, instale:")
        print("  pip install pip-audit")
        print("  pip audit")
        return None

def generate_report():
    """Gera relatório completo"""
    print_header("📊 RELATÓRIO DE DEPENDÊNCIAS - AULASHACK")
    
    print(f"Data: {datetime.now().strftime('%d de %B de %Y às %H:%M:%S')}")
    print(f"Python: {sys.version}")
    print()
    
    # Verificar versão Python
    major, minor = check_python_version()
    
    # Listar pacotes
    packages = check_installed_packages()
    
    # Verificar atualizações
    outdated = check_outdated_packages()
    
    # Verificar vulnerabilidades
    vuln = check_vulnerabilities()
    
    # Resumo final
    print_header("📋 RESUMO E RECOMENDAÇÕES")
    
    recommendations = []
    
    if major < 3 or (major == 3 and minor < 9):
        recommendations.append(f"❌ Atualizar Python para 3.9+ (Você tem {major}.{minor})")
    elif major == 3 and minor < 12:
        recommendations.append(f"⚠️ Considerar atualizar para Python 3.12+ (Você tem {major}.{minor})")
    else:
        recommendations.append(f"✅ Python {major}.{minor} está bom")
    
    if outdated:
        recommendations.append(f"⚠️ {len(outdated)} pacote(s) para atualizar")
    else:
        recommendations.append("✅ Todos os pacotes estão atualizados")
    
    if vuln is False:
        recommendations.append("❌ Vulnerabilidades encontradas - ATUALIZAR URGENTE")
    elif vuln is True:
        recommendations.append("✅ Nenhuma vulnerabilidade de segurança")
    else:
        recommendations.append("⚠️ Instale pip-audit para verificar vulnerabilidades")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    print("\n" + "="*80)
    print("\n✅ Relatório gerado com sucesso!\n")

if __name__ == '__main__':
    try:
        generate_report()
    except KeyboardInterrupt:
        print("\n\n⚠️ Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        sys.exit(1)