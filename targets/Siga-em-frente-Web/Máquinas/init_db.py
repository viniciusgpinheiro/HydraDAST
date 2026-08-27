from siga import app, db
from models import User, Booth
import random
import string

def generate_random_password(length=12):
    """Gera uma senha aleatória"""
    characters = string.ascii_letters + string.digits + '!@#$'
    return ''.join(random.choice(characters) for _ in range(length))

def init_database():
    """Inicializa o banco de dados com usuários e cabines"""
    
    with app.app_context():
        # Limpar banco existente
        db.drop_all()
        db.create_all()
        
        # Criar 3 cabines
        booth_data = [
            {'booth_number': 1, 'total_vehicles': 145, 'total_cash': 2850.50, 'pix_key': 'cabine1@sigaemfrente.com.br'},
            {'booth_number': 2, 'total_vehicles': 132, 'total_cash': 2640.75, 'pix_key': 'cabine2@sigaemfrente.com.br'},
            {'booth_number': 3, 'total_vehicles': 156, 'total_cash': 3120.25, 'pix_key': 'cabine3@sigaemfrente.com.br'}
        ]
        
        booths = []
        for booth_info in booth_data:
            booth = Booth(**booth_info)
            db.session.add(booth)
            booths.append(booth)
        
        db.session.commit()
        
        # Senhas dos usuários administrativos (aleatórias)
        admin_passwords = {
            'mario': generate_random_password(),
            'bruno': generate_random_password()
        }
        
        print("\n=== SENHAS DOS ADMINISTRADORES ===")
        for admin, password in admin_passwords.items():
            print(f"Usuário: {admin} | Senha: {password}")
        print("===================================\n")
        
        # Criar usuários administrativos
        admin_users = [
            User(id=101, username='mario', password=admin_passwords['mario'], role='admin', 
                 full_name='Mario Silva', phone='11-98765-4321'),
            User(username='bruno', password=admin_passwords['bruno'], role='admin', 
                 full_name='Bruno Santos', phone='11-99876-5432')
        ]
        
        for user in admin_users:
            db.session.add(user)
        
        db.session.commit()
        
        # Dados dos operadores
        operator_data = [
            # Cabine 1
            {'username': 'Igor', 'password': 'oper1-cab1', 'full_name': 'Igor Oliveira', 'booth_id': 1, 'phone': '11-91234-5678'},
            {'username': 'Tiago', 'password': 'oper2-cab1', 'full_name': 'Tiago Ferreira', 'booth_id': 1, 'phone': '11-92345-6789'},
            {'username': 'Yuri', 'password': 'oper3-cab1', 'full_name': 'Yuri Barbosa', 'booth_id': 1, 'phone': '11-93456-7890'},
            # Cabine 2
            {'username': 'Juan', 'password': 'oper4-cab2', 'full_name': 'Juan Rodriguez', 'booth_id': 2, 'phone': '11-94567-8901'},
            {'username': 'Max', 'password': 'oper5-cab2', 'full_name': 'Max Schneider', 'booth_id': 2, 'phone': '11-95678-9012'},
            {'username': 'Val', 'password': 'oper6-cab2', 'full_name': 'Valentina Costa', 'booth_id': 2, 'phone': '11-96789-0123'},
            # Cabine 3
            {'username': 'Amanda', 'password': 'oper7-cab3', 'full_name': 'Amanda Gomes', 'booth_id': 3, 'phone': '11-97890-1234'},
            {'username': 'Maria', 'password': 'oper8-cab3', 'full_name': 'Maria Souza', 'booth_id': 3, 'phone': '11-98901-2345'},
            {'username': 'Cris', 'password': 'oper9-cab3', 'full_name': 'Cristina Martins', 'booth_id': 3, 'phone': '11-99012-3456'}
        ]
        
        operator_users = []
        for i, operator_info in enumerate(operator_data, start=1):
            user = User(id=i, username=operator_info['username'], password=operator_info['password'], 
                       role='operator', booth_id=operator_info['booth_id'], full_name=operator_info['full_name'],
                       phone=operator_info['phone'])
            db.session.add(user)
            operator_users.append(user)
        
        db.session.commit()
        
        print("✓ Banco de dados inicializado com sucesso!")
        print(f"✓ 2 usuários administradores criados")
        print(f"✓ 9 operadores criados (3 por cabine)")
        print(f"✓ 3 cabines de pedágio criadas")

if __name__ == '__main__':
    init_database()