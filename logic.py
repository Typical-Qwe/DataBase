import sqlite3
from config import DATABASE

skills = [(_,) for _ in (['Python', 'SQL', 'API', 'Telegram'])]
statuses = [(_,) for _ in ([
    'На этапе проектирования',
    'В процессе разработки',
    'Разработан. Готов к использованию.',
    'Обновлен',
    'Завершен. Не поддерживается'
])]


class DB_Manager:
    def __init__(self, database):
        self.database = database

    def create_tables(self):
        connection = sqlite3.connect(self.database)
        with connection:
            connection.execute('''CREATE TABLE projects(
                project_id INTEGER PRIMARY KEY,
                user_id INTEGER,
                project_name TEXT NOT NULL,
                description TEXT,
                url TEXT,
                status_id INTEGER,
                photo TEXT,
                FOREIGN KEY (status_id) REFERENCES status(status_id)
            )''')

            connection.execute('''CREATE TABLE status(
                status_id INTEGER PRIMARY KEY,
                status_name TEXT
            )''')

            connection.execute('''CREATE TABLE skills(
                skill_id INTEGER PRIMARY KEY,
                skill_name TEXT
            )''')

            connection.execute('''CREATE TABLE project_skills(
                project_id INTEGER,
                skill_id INTEGER,
                FOREIGN KEY (skill_id) REFERENCES skills(skill_id),
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            )''')

            connection.commit()

    def add_photo_column(self):
        conn = sqlite3.connect(self.database)
        with conn:
            try:
                conn.execute("ALTER TABLE projects ADD COLUMN photo TEXT")
            except sqlite3.OperationalError:
                pass

    def __executemany(self, sql, data):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.executemany(sql, data)
            conn.commit()

    def __select_data(self, sql, data=tuple()):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            return cur.fetchall()

    def default_insert(self):
        sql = 'INSERT OR IGNORE INTO skills (skill_name) values(?)'
        self.__executemany(sql, skills)

        sql = 'INSERT OR IGNORE INTO status (status_name) values(?)'
        self.__executemany(sql, statuses)

    def insert_project(self, data):
        sql = """INSERT INTO projects
        (user_id, project_name, url, status_id)
        values(?, ?, ?, ?)"""
        self.__executemany(sql, data)

    def update_project_photo(self, user_id, project_name, photo):
        sql = """
        UPDATE projects
        SET photo = ?
        WHERE project_name = ? AND user_id = ?
        """
        self.__executemany(sql, [(photo, project_name, user_id)])

    def insert_skill(self, user_id, project_name, skill):
        sql = 'SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?'
        project_id = self.__select_data(sql, (project_name, user_id))[0][0]

        skill_id = self.__select_data(
            'SELECT skill_id FROM skills WHERE skill_name = ?',
            (skill,)
        )[0][0]

        data = [(project_id, skill_id)]
        sql = 'INSERT OR IGNORE INTO project_skills VALUES(?, ?)'
        self.__executemany(sql, data)

    def get_statuses(self):
        sql = "SELECT status_name FROM status"
        return self.__select_data(sql)

    def get_status_id(self, status_name):
        sql = 'SELECT status_id FROM status WHERE status_name = ?'
        res = self.__select_data(sql, (status_name,))
        if res:
            return res[0][0]
        return None

    def get_projects(self, user_id):
        sql = """SELECT * FROM projects WHERE user_id = ?"""
        return self.__select_data(sql, (user_id,))

    def get_project_id(self, project_name, user_id):
        return self.__select_data(
            'SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?',
            (project_name, user_id)
        )[0][0]

    def get_skills(self):
        return self.__select_data('SELECT * FROM skills')

    def get_project_skills(self, project_name):
        res = self.__select_data('''
        SELECT skill_name FROM projects
        JOIN project_skills ON projects.project_id = project_skills.project_id
        JOIN skills ON skills.skill_id = project_skills.skill_id
        WHERE project_name = ?
        ''', (project_name,))
        return ', '.join([x[0] for x in res])

    def get_project_info(self, user_id, project_name):
        sql = """
        SELECT project_name, description, url, status_name, photo
        FROM projects
        JOIN status ON status.status_id = projects.status_id
        WHERE project_name=? AND user_id=?
        """
        return self.__select_data(sql, (project_name, user_id))

    def update_projects(self, param, data):
        sql = f"""UPDATE projects SET {param} = ?
        WHERE project_name = ? AND user_id = ?"""
        self.__executemany(sql, [data])

    def delete_project(self, user_id, project_id):
        sql = """DELETE FROM projects
        WHERE user_id = ? AND project_id = ?"""
        self.__executemany(sql, [(user_id, project_id)])

    def delete_skill(self, project_id, skill_id):
        sql = """DELETE FROM project_skills
        WHERE project_id = ? AND skill_id = ?"""
        self.__executemany(sql, [(project_id, skill_id)])


if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    manager.default_insert()
    # manager.add_photo_column()
    # manager.insert_project([(1, "Telegram bot with DB", "http://kodland.org", 3)])
    # manager.update_project_photo(1, "Telegram bot with DB", "photos/bot_project.jpg")
    # manager.update_projects('description', ("Ура, это описание", "Telegram bot with DB", 1))