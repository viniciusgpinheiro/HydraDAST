#!/usr/bin/env python3
"""
Script para descobrir e exibir informações de rede local
Útil para saber qual URL usar para acessar a aplicação de outra máquina
"""

import socket
import sys

def get_local_ip():
    """
    Detecta automaticamente o IP local da máquina.
    Tenta vários métodos para garantir o resultado correto.
    """
    try:
        # Método 1: Conectar a um servidor externo (sem realmente enviar dados)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            # Método 2: Usar gethostbyname
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            if ip != '127.0.0.1':
                return ip
        except Exception:
            pass
    
    # Fallback: retornar localhost
    return '127.0.0.1'

def get_hostname():
    """Obtém o nome da máquina"""
    try:
        return socket.gethostname()
    except Exception:
        return "Desconhecido"

def main():
    print("\n" + "="*80)
    print("🌐 INFORMAÇÕES DE REDE - SIGA EM FRENTE")
    print("="*80)
    print()
    
    # Obter informações
    hostname = get_hostname()
    local_ip = get_local_ip()
    
    print(f"🖥️  Nome da Máquina:     {hostname}")
    print(f"📍 IP Local (IPv4):     {local_ip}")
    print()
    print("="*80)
    print()
    print("📱 COMO ACESSAR A APLICAÇÃO:")
    print()
    print(f"  ✅ De ESTA máquina:")
    print(f"     http://127.0.0.1:5001")
    print()
    print(f"  ✅ De OUTRA máquina na rede local:")
    print(f"     http://{local_ip}:5001")
    print()
    print("="*80)
    print()
    print("💡 EXEMPLOS DE USO:")
    print()
    print(f"  • VM Linux na mesma rede:")
    print(f"    curl -I http://{local_ip}:5001")
    print()
    print(f"  • Burp Suite / Proxy:")
    print(f"    http://{local_ip}:5001")
    print()
    print(f"  • Outro computador Windows:")
    print(f"    http://{local_ip}:5001")
    print()
    print("="*80)
    print()
    
    # Instruções para firewall
    print("⚠️  NOTAS IMPORTANTES:")
    print()
    print("  1. A aplicação está escutando em TODAS as interfaces (0.0.0.0:5001)")
    print()
    print("  2. Se não conseguir acessar de outra máquina:")
    print("     • Verifique o firewall do Windows")
    print("     • Abra a porta 5001 no firewall Windows")
    print("     • Verifique se estão na mesma rede local")
    print()
    print("  3. No Windows Defender Firewall:")
    print("     → Configurações > Firewall do Windows > Permitir app")
    print("     → Clique em 'Permitir outro app...'")
    print("     → Selecione python.exe ou a aplicação")
    print("     → Marque 'Privada' (para rede local)")
    print()
    print("="*80)
    print()

if __name__ == '__main__':
    main()
