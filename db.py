import sqlite3


class SQLiteClient:
    def __init__(self, file: str):
        self.file = file
        self.conn = None
        self.cur = None

    def create_conn(self):
        self.conn = sqlite3.connect(self.file, check_same_thread=False)  # объект коннекта будет создаваться в том же
        # самом потоке, что и основной поток

    def close_conn(self):
        self.conn.close()

    def execute_query(self, query: str, params: tuple):
        if self.conn is not None:
            self.conn.execute(query, params)
            self.conn.commit()
        else:
            raise ConnectionError('no connection to database')

    def execute_select_query(self, query: str):
        if self.conn is not None:
            cur = self.conn.cursor()
            cur.execute(query)
            return cur.fetchall()
        else:
            raise ConnectionError('no connection to database')


class TaskAction:
    CREATE_TASK = """
        INSERT INTO tasks (task_id, task_name, task_description, creation_date, deadline, done, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """

    GET_TASK_BY_NAME = """
        SELECT task_id, task_name, task_description, creation_date, deadline, done
        FROM tasks WHERE task_name = %r and user_id = %s;
    """

    GET_TASK_BY_DATE = """
        SELECT task_id, task_name, task_description, creation_date, deadline, done
        FROM tasks WHERE creation_date = %r and user_id = %s;
    """

    GET_TASK_BY_DEADLINE = """
        SELECT task_id, task_name, task_description, creation_date, deadline, done
        FROM tasks WHERE deadline = %r and user_id = %s;
    """

    GET_TASK_BY_STATUS = """
        SELECT task_id, task_name, task_description, creation_date, deadline, done
        FROM tasks WHERE done = %s and user_id = %s;
    """

    GET_ID = """
        SELECT task_id FROM tasks ORDER BY task_id DESC LIMIT 1
    """

    DONE_TASK = """
        UPDATE tasks SET done=1 WHERE task_name = ? and user_id = ?;
    """

    def __init__(self, db_client: SQLiteClient):
        self.db_client = db_client

    def setup(self):
        self.db_client.create_conn()

    def shutdown(self):
        self.db_client.close_conn()

    def create_task(self, task_id: int, task_name: str, task_description: str,
                    creation_date: str, deadline: str, done: int, user_id: int):
        self.db_client.execute_query(self.CREATE_TASK, (task_id, task_name, task_description,
                                                        creation_date, deadline, done, user_id))

    def get_task_by_name(self, task_name: str, user_id: int):
        task = self.db_client.execute_select_query(self.GET_TASK_BY_NAME % (task_name, user_id))
        return task[0] if task else []

    def get_task_by_date(self, creation_date: str, user_id: int):
        task = self.db_client.execute_select_query(self.GET_TASK_BY_DATE % (creation_date, user_id))
        return task if task else []

    def get_task_by_deadline(self, deadline: str, user_id: int):
        task = self.db_client.execute_select_query(self.GET_TASK_BY_DEADLINE % (deadline, user_id))
        return task if task else []

    def get_task_by_status(self, status: int, user_id: int):
        task = self.db_client.execute_select_query(self.GET_TASK_BY_STATUS % (status, user_id))
        return task if task else []

    def find_id(self):
        return int(self.db_client.execute_select_query(self.GET_ID)[0][0])

    def done_task(self, task_name: str, user_id: int):
        self.db_client.execute_query(self.DONE_TASK, (task_name, user_id))


if __name__ == '__main__':
    sqlite_client = SQLiteClient('tasks.db')
    sqlite_client.create_conn()
    task_action = TaskAction(SQLiteClient('tasks.db'))
    task_action.setup()
    task_new = {'task_id': 2, 'task_name': 'second task', 'task_description': 'so much work!',
                'creation_date': '2023-10-10', 'deadline': '2023-11-10', 'done': 0, 'user_id': 286742350}
    task_action.create_task(**task_new)
