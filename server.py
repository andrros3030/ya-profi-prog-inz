import os
import random
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.serving import WSGIRequestHandler
from flask_restful import Api
from flask_restful_swagger import swagger

app = Flask(__name__)
db = SQLAlchemy(app)
api = Api(app)


def generate_id():
    return int(''.join([str(random.randint(1, 9)) for _ in range(10)]))

@swagger.operation(
        notes='В зависимости от метода: создаёт новую промоакцию или выводит данные про все промоакции',
        nickname='promo',
        parameters=[
            {
              "name": "name",
              "description": "Название промоакции",
              "required": True,
              "paramType": "Строка до 255 символов"
            },
            {
              "name": "description",
              "description": "Описание промоакции",
              "required": False,
              "paramType": "Строка до 4000 символов"
            },
          ],
        responseMessages=[
            {
              "code": 201,
              "message": "Промоакция создана, возвращен id промоакции"
            },
            {
              "code": 500,
              "message": "На сервере возникла ошибка при обработке запроса"
            }
          ]
        )
@app.route('/promo', methods=['POST', 'GET'])
def promo():
    """
    POST:
    Создает промоакцию с заданными данными
    Поле "name" обязательно, поле "description" опционально

    GET:
    Получение краткой информации (без информации об участниках и призах) обо всех промоакциях
    """
    if request.method == 'POST':
        try:
            # print('here')
            requestData = request.get_json()
            # print(requestData)
            name = requestData['name']
            desc = ''
            if 'description' in requestData.keys():
                desc = requestData['description']
            new_id = generate_id()
            # print(new_id)
            db.engine.execute("INSERT INTO PROMOACTIONS(PK_ID, V_NAME, V_DESC) VALUES('{}','{}', '{}')".format(
                new_id,
                name,
                desc
            ))
            return str(new_id), 201
        except Exception as e:
            return str(e), 500
    else:
        querry = [
            {'id': el[0], 'name': el[1],
             'description': el[2]} for el in db.engine.execute('SELECT PK_ID, V_NAME, V_DESC '
                                                               'from PROMOACTIONS').fetchall()
        ]
        print(querry)
        return {"body": querry}, 200


@swagger.operation(
        notes='Выводит все данные и позволяет модифицировать промоакцию по заданному идентификатору промоакции',
        nickname='promo_by_id',
        parameters=[
            {
              "name": "id",
              "description": "Идентификатор промоакции",
              "required": True,
              "paramType": "Натуральное число"
            },
            {
              "name": "name",
              "description": "Новое название промоакции",
              "required": False,
              "paramType": "Строка до 255 символов"
            },
            {
              "name": "description",
              "description": "Новое описание промоакции",
              "required": False,
              "paramType": "Строка до 4000 символов"
            },
          ],
        responseMessages=[
            {
              "code": 200,
              "message": "(GET) Возвращены данные промоакции по заданному идентификатору"
            },
            {
                "code": 202,
                "message": "(PUT, DELETE) Применено"
            },
            {
                "code": 404,
                "message": "(GET) Промоакция не найдена, проверьте идентификатор"
            },
            {
              "code": 500,
              "message": "На сервере возникла ошибка при обработке запроса"
            }
          ]
        )
@app.route('/promo/<id>', methods=['GET', 'PUT', 'DELETE'])
def promo_by_id(id):
    """
    GET:
    Получение полной информации (с информацией об участниках и призах) о промоакции по идентификатору

    PUT:
    Редактирование промо-акции по идентификатору промо-акции

    DELETE:
    Удаление промоакции по идентификатору

    :return:
    200 - (GET) Возвращены данные промоакции по заданному идентификатору
    202 - (PUT, DELETE) Применено
    404 - (GET) Промоакция не найдена, проверьте идентификатор
    500 - На сервере возникла ошибка
    """
    if request.method == 'GET':
        querry = db.engine.execute('SELECT PK_ID, V_NAME, V_DESC '
                                   'from PROMOACTIONS '
                                   "where PK_ID = {}".format(id)).fetchall()
        if len(querry) == 0:
            return 'Not found', 404
        result = {
            'id': querry[0][0],
            'name': querry[0][1],
            'description': querry[0][2],
            'prizes': [{
                'id': el[0],
                'name': el[1]
            } for el in db.engine.execute("SELECT prz.PK_ID, prz.V_DESC FROM "
                                          "PROMO_PRIZES linker join "
                                          "PRIZES prz on linker.FK_PRIZE = prz.PK_ID "
                                          "where linker.FK_PROMO = {}".format(id)).fetchall()],
            'participants': [{
                'id': el[0],
                'name': el[1]
            } for el in db.engine.execute("SELECT part.PK_ID, part.V_NAME FROM "
                                          "PROMO_PARTICIPANTS linker join "
                                          "PARTICIPANTS part on linker.FK_PART = part.PK_ID "
                                          "where linker.FK_PROMO = {}".format(id)).fetchall()],
        }
        print(result)
        return {"body": result}, 200
    elif request.method == 'PUT':
        try:
            requestData = request.get_json()
            name = ''
            if 'name' in requestData.keys():
                name = requestData['name']
            desc = ''
            if 'description' in requestData.keys():
                desc = requestData['description']
            if len(name) > 0:
                db.engine.execute("UPDATE PROMOACTIONS "
                                  "SET V_NAME = '{}', "
                                  "V_DESC = '{}' "
                                  "where PK_ID = {}".format(name, desc, id))
            else:
                db.engine.execute("UPDATE PROMOACTIONS "
                                  "SET V_DESC = '{}' "
                                  "where PK_ID = {}".format(desc, id))
            return 'Ok', 202
        except Exception as e:
            print(str(e))
            return str(e), 500
    else:
        try:
            db.engine.execute("DELETE FROM PROMOACTIONS WHERE PK_ID = {}".format(id))
            return 'Ok', 202
        except Exception as e:
            print(str(e))
            return str(e), 500


@swagger.operation(
        notes='Добавляет нового участника к промоакции с данным идентификатором <id>',
        nickname='add_participant',
        parameters=[
            {
              "name": "id",
              "description": "Идентификатор промоакции",
              "required": True,
              "paramType": "Натуральное число"
            },
            {
              "name": "name",
              "description": "Имя участника",
              "required": True,
              "paramType": "Строка до 255 символов"
            },
          ],
        responseMessages=[
            {
              "code": 201,
              "message": "Участник успешно добавлен к промоакции"
            },
            {
              "code": 500,
              "message": "На сервере возникла ошибка при обработке запроса"
            }
          ]
        )
@app.route('/promo/<id>/participant', methods=['POST'])
def add_participant(id):
    """
    Добавляет нового участника к промоакции с данным идентификатором <id>
    Обязательное поле "name"
    :return:
    201 - Участник успешно добавлен к промоакции
    500 - На сервер возникла ошибка
    """
    try:
        requestData = request.get_json()
        name = requestData['name']
        new_id = generate_id()
        db.engine.execute("INSERT INTO PARTICIPANTS(PK_ID, V_NAME) VALUES('{}', '{}')".format(new_id, name))
        db.engine.execute("INSERT INTO PROMO_PARTICIPANTS(PK_ID,FK_PROMO,FK_PART) VALUES('{}', '{}', '{}')".format(
            generate_id(), id, new_id
        ))
        return str(new_id), 201
    except Exception as e:
        print(str(e))
        return str(e), 500


@swagger.operation(
        notes='Удаляет участника из промоакции по идентификаторам промоакции и участника',
        nickname='remove_participant',
        parameters=[
            {
              "name": "promoId",
              "description": "Идентификатор промоакции",
              "required": True,
              "paramType": "Натуральное число"
            },
            {
              "name": "participantId",
              "description": "Идентификатор участника промоакции",
              "required": True,
              "paramType": "Натуральное число"
            }
          ],
        responseMessages=[
            {
              "code": 202,
              "message": "Изменения применены"
            },
            {
              "code": 500,
              "message": "На сервере возникла ошибка при обработке запроса"
            }
          ]
        )
@app.route('/promo/<promoId>/participant/<participantId>', methods=['DELETE'])
def remove_participant(promoId, participantId):
    """
    Удаляет участника из промоакции по идентификаторам промоакции и участника
    :return:
    202 - Изменения применены
    500 - На сервере возникла ошибка
    """
    try:
        db.engine.execute("DELETE FROM PROMO_PARTICIPANTS "
                          "WHERE FK_PART={} "
                          "AND FK_PROMO={}".format(participantId, promoId))
        return 'Ok', 202
    except Exception as e:
        print(str(e))
        return str(e), 500


@swagger.operation(
        notes='Добавляет в промоакцию по идентификатору приз',
        nickname='add_prize',
        parameters=[
            {
              "name": "id",
              "description": "Идентификатор промоакции",
              "required": True,
              "paramType": "Натуральное число"
            },
            {
              "name": "description",
              "description": "Описание приза",
              "required": True,
              "paramType": "Строка до 4000 символов"
            },
          ],
        responseMessages=[
            {
              "code": 201,
              "message": "Приз успешно добавлен к промоакции"
            },
            {
              "code": 500,
              "message": "На сервере возникла ошибка при обработке запроса"
            }
          ]
        )
@app.route('/promo/<id>/prize', methods=['POST'])
def add_prize(id):
    """
    Добавляет в промоакцию по идентификатору <id> приз с обязательным полем "description"
    :return:
    201 - Приз успешно добавлен к промоакции
    500 - На сервере возникла ошибка
    """
    try:
        requestData = request.get_json()
        name = requestData['description']
        new_id = generate_id()
        db.engine.execute("INSERT INTO PRIZES(PK_ID, V_DESC) VALUES('{}', '{}')".format(new_id, name))
        db.engine.execute("INSERT INTO PROMO_PRIZES(PK_ID,FK_PROMO,FK_PRIZE) VALUES('{}', '{}', '{}')".format(
            generate_id(), id, new_id
        ))
        return str(new_id), 201
    except Exception as e:
        print(str(e))
        return str(e), 500


@swagger.operation(
        notes='Удаляет приз из промоакции по идентификаторам промоакции и участника',
        nickname='remove_prize',
        parameters=[
            {
              "name": "promoId",
              "description": "Идентификатор промоакции",
              "required": True,
              "paramType": "Натуральное число"
            },
            {
              "name": "prizeId",
              "description": "Идентификатор приза промоакции",
              "required": True,
              "paramType": "Натуральное число"
            }
          ],
        responseMessages=[
            {
              "code": 202,
              "message": "Изменения применены"
            },
            {
              "code": 500,
              "message": "На сервере возникла ошибка при обработке запроса"
            }
          ]
        )
@app.route('/promo/<promoId>/prize/<prizeId>', methods=['DELETE'])
def remove_prize(promoId, prizeId):
    """
    Удаляет приз из промоакции по идентификаторам промоакции и приза
    :return:
    202 - Изменения применены
    500 - На сервере возникла ошибка
    """
    try:
        db.engine.execute("DELETE FROM PROMO_PRIZES "
                          "WHERE FK_PRIZE={} "
                          "AND FK_PROMO={}".format(prizeId, promoId))
        return 'Ok', 202
    except Exception as e:
        print(str(e))
        return str(e), 500


@swagger.operation(
        notes='Проводит розыгрыш для промоакции по идентафикатору',
        nickname='raffle',
        parameters=[
            {
              "name": "promoId",
              "description": "Идентификатор промоакции",
              "required": True,
              "paramType": "Натуральное число"
            }
          ],
        responseMessages=[
            {
              "code": 201,
              "message": "Розыгрыш проведен, возвращены результаты розыгрыша"
            },
            {
              "code": 409,
              "message": "Conflict: Проведение розыгрыша невозможно, число участников не соответствует числу призов"
            },
            {
              "code": 500,
              "message": "На сервере возникла ошибка при обработке запроса"
            }
          ]
        )
@app.route('/promo/<id>/raffle', methods=['POST'])
def raffle(id):
    """
    Проводит розыгрыш для промоакции по идентафикатору <id>
    :return:
    {"body":List}, 201 - Розыгрыш проведен, возвращены результаты розыгрыша
    "Conflict", 409 - Проведение розыгрыша невозможно, число участников не соответствует числу призов
    "Error", 500 - На сервере возникла ошибка при проведении розыгрыша
    """
    try:
        prizes = db.engine.execute("SELECT prz.PK_ID, prz.V_DESC "
                                   "FROM PROMO_PRIZES prpr join "
                                   "PRIZES prz on prpr.FK_PRIZE = prz.PK_ID "
                                   "WHERE prpr.FK_PROMO = {}".format(id)).fetchall()
        participants = db.engine.execute("SELECT part.PK_ID, part.V_NAME "
                                         "FROM PROMO_PARTICIPANTS prpr join "
                                         "PARTICIPANTS part on prpr.FK_PART = part.PK_ID "
                                         "WHERE prpr.FK_PROMO = {}".format(id)).fetchall()
        if len(prizes) != len(participants):
            return 'Conflict', 409
        result = [{"winner": {
            "id": participants[i][0],
            "name": participants[i][1]
        },
                   "prize": {
                       "id": prizes[i][0],
                       "description": prizes[i][1]
                   }
                   } for i in range(len(prizes))]
        return {'body': result}, 201
    except Exception as e:
        print(str(e))
        return str(e), 500


def initDB():
    """
    Инициализирует базу данных для последующей работы с ней.
    """
    db_path = os.path.join(os.path.dirname(__file__), 'app.db')
    db_uri = 'sqlite:///{}'.format(db_path)
    db = SQLAlchemy(app)
    db.create_all()
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    if len(list(db.engine.execute("SELECT * FROM sqlite_master where type = 'table'").fetchall())) < 6:
        db.engine.execute("""
        CREATE TABLE PROMOACTIONS(
    PK_ID      INT NOT NULL,
    V_NAME     VARCHAR(255) NOT NULL,
    V_DESC     VARCHAR(4000) NULL,
    PRIMARY KEY (PK_ID)
);""")
        db.engine.execute("""
        CREATE TABLE PRIZES(
    PK_ID       INT NOT NULL,
    V_DESC      VARCHAR(4000) NULL,
    PRIMARY KEY (PK_ID)
);""")
        db.engine.execute("""
        CREATE TABLE PROMO_PRIZES(
    PK_ID       INT NOT NULL,
    FK_PROMO    INT NOT NULL,
    FK_PRIZE    INT NOT NULL,
    PRIMARY KEY (PK_ID),
    FOREIGN KEY (FK_PRIZE) REFERENCES PRIZES (PK_ID) ON DELETE CASCADE,
    FOREIGN KEY (FK_PROMO) REFERENCES PROMOACTIONS (PK_ID) ON DELETE CASCADE
);
""")
        db.engine.execute("""
        CREATE TABLE PARTICIPANTS(
    PK_ID       INT NOT NULL,
    V_NAME      VARCHAR(255) NOT NULL,
    PRIMARY KEY (PK_ID)
);
""")
        db.engine.execute("""
        CREATE TABLE PROMO_PARTICIPANTS(
    PK_ID       INT NOT NULL,
    FK_PROMO    INT NOT NULL,
    FK_PART    INT NOT NULL,
    PRIMARY KEY (PK_ID),
    FOREIGN KEY (FK_PART) REFERENCES PARTICIPANTS (PK_ID) ON DELETE CASCADE,
    FOREIGN KEY (FK_PROMO) REFERENCES PROMOACTIONS (PK_ID) ON DELETE CASCADE
);
""")


initDB()

if __name__ == "__main__":
    WSGIRequestHandler.protocol_version = "HTTP/1.1"
    app.run(host='0.0.0.0', port=8080, threaded=True)
