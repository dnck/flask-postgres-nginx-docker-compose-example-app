import models as db
import service


def server_set_up():
    db.initialize_db_with_extension_and_tables()
    service.app.run(debug=True)

if __name__=='__main__':
    server_set_up()
