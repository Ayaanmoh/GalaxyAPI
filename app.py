import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'galaxies.db')
app.config['JWT_SECRET_KEY'] = 'secretkey'
app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']

db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)


@app.cli.command('db_create')
def db_create():
    db.create_all()


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()


@app.cli.command('db_seed')
def db_seed():
    mw = Galaxy(galaxy_name='MilkyWay',
                     galaxy_type='spiral',
                     home_star='Astar',
                     mass=1.5,
                     distance=25000)

    andr = Galaxy(galaxy_name='Andromeda',
                         galaxy_type='spiral',
                         home_star='M31',
                         mass=1.230,
                         distance=2.537)

    mess = Galaxy(galaxy_name='Messier81',
                     galaxy_type='sbspiral',
                     home_star='M81',
                     mass=5.97,
                     distance=92.9)

    db.session.add(mw)
    db.session.add(andr)
    db.session.add(mess)

    test_user = User(first_name='Ayaan',
                     last_name='Mohammed',
                     email='sample@test.com',
                     password='Password1')

    db.session.add(test_user)
    db.session.commit()



@app.route('/not_found')
def not_found():
    return jsonify(message='Not found'), 404


@app.route('/parameters')
def parameters():
    name = request.args.get('name')
    age = int(request.args.get('age'))
    if age < 18:
        return jsonify(message="Age restricted"), 401
    else:
        return jsonify(message="Welcome!")


@app.route('/url_variables/<string:name>/<int:age>')
def url_variables(name: str, age: int):
    if age < 18:
        return jsonify(message="Age restriction"), 401
    else:
        return jsonify(message="Welcome!")


@app.route('/galaxies', methods=['GET'])
def galaxies():
    galaxies_list = galaxy.query.all()
    result = galaxies_schema.dump(galaxies_list)
    return jsonify(result.data)


@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(message='Email already exists.'), 409
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        user = User(first_name=first_name, last_name=last_name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify(message="User created successfully."), 201


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']

    test = User.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message="Login successful!", access_token=access_token)
    else:
        return jsonify(message="Invalid email or password"), 401


@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email: str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message("API password is " + user.password,
                      sender="admin@api.com",
                      recipients=[email])
        mail.send(msg)
        return jsonify(message="Password sent to " + email)
    else:
        return jsonify(message="Email doesn't exist"), 401


@app.route('/galaxy_details/<int:galaxy_id>', methods=["GET"])
def galaxy_details(galaxy_id: int):
    galaxy = galaxy.query.filter_by(galaxy_id=galaxy_id).first()
    if galaxy:
        result = galaxy_schema.dump(galaxy)
        return jsonify(result.data)
    else:
        return jsonify(message="Galaxy does not exist"), 404


@app.route('/add_galaxy', methods=['POST'])
@jwt_required
def add_galaxy():
    galaxy_name = request.form['galaxy_name']
    test = galaxy.query.filter_by(galaxy_name=galaxy_name).first()
    if test:
        return jsonify("There is already a galaxy by that name"), 409
    else:
        galaxy_type = request.form['galaxy_type']
        home_star = request.form['home_star']
        mass = float(request.form['mass'])
        distance = float(request.form['distance'])

        new_galaxy = galaxy(galaxy_name=galaxy_name,
                            galaxy_type=galaxy_type,
                            home_star=home_star,
                            mass=mass,
                            distance=distance)

        db.session.add(new_galaxy)
        db.session.commit()
        return jsonify(message="Galaxy added"), 201


@app.route('/update_galaxy', methods=['PUT'])
@jwt_required
def update_galaxy():
    galaxy_id = int(request.form['galaxy_id'])
    galaxy = galaxy.query.filter_by(galaxy_id=galaxy_id).first()
    if galaxy:
        galaxy.galaxy_name = request.form['galaxy_name']
        galaxy.galaxy_type = request.form['galaxy_type']
        galaxy.home_star = request.form['home_star']
        galaxy.mass = float(request.form['mass'])
        galaxy.distance = float(request.form['distance'])
        db.session.commit()
        return jsonify(message="Galaxy updated"), 202
    else:
        return jsonify(message="Galaxy does not exist"), 404


@app.route('/remove_galaxy/<int:galaxy_id>', methods=['DELETE'])
@jwt_required
def remove_galaxy(galaxy_id: int):
    galaxy = galaxy.query.filter_by(galaxy_id=galaxy_id).first()
    if galaxy:
        db.session.delete(galaxy)
        db.session.commit()
        return jsonify(message="You deleted a galaxy"), 202
    else:
        return jsonify(message="That galaxy does not exist"), 404


# database models
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class galaxy(db.Model):
    __tablename__ = 'galaxies'
    galaxy_id = Column(Integer, primary_key=True)
    galaxy_name = Column(String)
    galaxy_type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    distance = Column(Float)

class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')


class galaxieschema(ma.Schema):
    class Meta:
        fields = ('galaxy_id', 'galaxy_name', 'galaxy_type', 'home_star', 'mass', 'distance')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

galaxy_schema = galaxieschema()
galaxies_schema = galaxieschema(many=True)


if __name__ == '__main__':
    app.run()
