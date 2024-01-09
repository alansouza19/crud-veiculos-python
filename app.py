from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import jwt
from functools import wraps



app = Flask(__name__)
app.config['SECRET_KEY'] = '12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/cadastro-veiculos'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Veiculo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    marca = db.Column(db.String(50), nullable=False)
    modelo = db.Column(db.String(50), nullable=False)
    foto = db.Column(db.String(100), nullable=False)


def generate_token(email, password):
    chave_secreta = app.config['SECRET_KEY']

    payload = {
        'email': email,
        'password': password,
        'iat': datetime.utcnow(),  
    }

    expiracao = timedelta(seconds=3600)
    payload['exp'] = datetime.utcnow() + expiracao

    token = jwt.encode(payload, chave_secreta, algorithm='HS256')

    return token


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'message': 'Token de autenticação está faltando!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except:
            return jsonify({'message': 'Token de autenticação é inválido!'}), 401

        return f(*args, **kwargs)

    return decorated

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if data['email'] == 'usuario@email.com' and data['password'] == 'senha123':
        token = generate_token(data['email'], data['password'])  
        return jsonify({'token': token})

    return jsonify({'message': 'Credenciais inválidas'}), 401


@app.route('/veiculos', methods=['GET'])
@token_required
def get_veiculos():
    veiculos = Veiculo.query.all()

    veiculos_json = []
    for veiculo in veiculos:
        veiculo_data = {
            'id': veiculo.id,
            'nome': veiculo.nome,
            'marca': veiculo.marca,
            'modelo': veiculo.modelo,
            'foto': veiculo.foto
        }
        veiculos_json.append(veiculo_data)

    return jsonify({'veiculos': veiculos_json})


@app.route('/veiculos', methods=['POST'])
@token_required
def create_veiculo():
    data = request.get_json()

    novo_veiculo = Veiculo(
        nome=data['nome'],
        marca=data['marca'],
        modelo=data['modelo'],
        foto=data['foto']
    )

    db.session.add(novo_veiculo)
    db.session.commit()

    return jsonify({'message': 'Veículo criado com sucesso!'})

@app.route('/veiculos/<int:veiculo_id>', methods=['PUT'])
@token_required
def update_veiculo(veiculo_id):
    veiculo = Veiculo.query.get(veiculo_id)

    if not veiculo:
        return jsonify({'message': 'Veículo não encontrado!'}), 404

    data = request.get_json()

    veiculo.nome = data['nome']
    veiculo.marca = data['marca']
    veiculo.modelo = data['modelo']
    veiculo.foto = data['foto']

    db.session.commit()

    return jsonify({'message': 'Veículo atualizado com sucesso!'})

@app.route('/veiculos/<int:veiculo_id>', methods=['DELETE'])
@token_required
def delete_veiculo(veiculo_id):
    veiculo = Veiculo.query.get(veiculo_id)

    if not veiculo:
        return jsonify({'message': 'Veículo não encontrado!'}), 404

    db.session.delete(veiculo)
    db.session.commit()

    return jsonify({'message': 'Veículo excluído com sucesso!'})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)



