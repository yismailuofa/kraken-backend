import unittest

from fastapi.testclient import TestClient
from mongomock import MongoClient

from api.database import getDb
from api.main import app


class TestTasks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.mockDb = MongoClient().db
        app.dependency_overrides[getDb] = lambda: cls.mockDb

    def createUser(self, keyword: str):
        return self.client.post(
            "/users/register",
            json={
                "username": keyword,
                "password": keyword,
                "email": f"{keyword}@{keyword}.com",
            },
        ).json()

    def userToHeader(self, user):
        return {"Authorization": f"Bearer {user['token']}"}

    def createProject(self, user, name, description):
        return self.client.post(
            "/projects/",
            json={
                "name": name,
                "description": description,
            },
            headers=self.userToHeader(user),
        )

    def createMilestone(self, user, projectId, name, description, dueDate):
        return self.client.post(
            "/milestones/",
            json={
                "projectId": projectId,
                "name": name,
                "description": description,
                "dueDate": dueDate,
            },
            headers=self.userToHeader(user),
        )

    def createTask(
        self, user, projectId, milestoneId, name, description, dueDate, qaTask
    ):
        return self.client.post(
            "/tasks/",
            json={
                "projectId": projectId,
                "milestoneId": milestoneId,
                "name": name,
                "description": description,
                "dueDate": dueDate,
                "qaTask": qaTask,
            },
            headers=self.userToHeader(user),
        )

    def tearDown(self) -> None:
        self.mockDb.users.delete_many({})
        self.mockDb.projects.delete_many({})
        self.mockDb.milestones.delete_many({})
        self.mockDb.tasks.delete_many({})

    def testCreateTask(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()
        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        taskName = "test"
        taskDescription = "test"
        taskDueDate = "2022-01-01T00:00:00"
        qaTaskName = "qatest"
        qaTaskDescription = "qatest"
        qaTaskDueDate = "2022-01-01T00:00:00"

        taskResponse = self.createTask(
            user,
            project["id"],
            milestone["id"],
            taskName,
            taskDescription,
            taskDueDate,
            {
                "name": qaTaskName,
                "description": qaTaskDescription,
                "dueDate": qaTaskDueDate,
            },
        )

        self.assertEqual(taskResponse.status_code, 200)

        task = taskResponse.json()

        self.assertEqual(task["projectId"], project["id"])
        self.assertEqual(task["milestoneId"], milestone["id"])
        self.assertEqual(task["name"], taskName)
        self.assertEqual(task["description"], taskDescription)
        self.assertEqual(task["dueDate"], taskDueDate)
        self.assertEqual(task["qaTask"]["name"], qaTaskName)
        self.assertEqual(task["qaTask"]["description"], qaTaskDescription)
        self.assertEqual(task["qaTask"]["dueDate"], qaTaskDueDate)

        for v in task.values():
            self.assertIsNotNone(v)

    def testGetTask(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()
        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        taskName = "test"
        taskDescription = "test"
        taskDueDate = "2022-01-01T00:00:00"
        qaTaskName = "qatest"
        qaTaskDescription = "qatest"
        qaTaskDueDate = "2022-01-01T00:00:00"

        createTaskResponse = self.createTask(
            user,
            project["id"],
            milestone["id"],
            taskName,
            taskDescription,
            taskDueDate,
            {
                "name": qaTaskName,
                "description": qaTaskDescription,
                "dueDate": qaTaskDueDate,
            },
        )

        self.assertEqual(createTaskResponse.status_code, 200)

        task = createTaskResponse.json()

        getTaskResponse = self.client.get(
            f"/tasks/{task['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(getTaskResponse.status_code, 200)

        task = getTaskResponse.json()

        self.assertEqual(task["projectId"], project["id"])
        self.assertEqual(task["milestoneId"], milestone["id"])
        self.assertEqual(task["name"], taskName)
        self.assertEqual(task["description"], taskDescription)
        self.assertEqual(task["dueDate"], taskDueDate)
        self.assertEqual(task["qaTask"]["name"], qaTaskName)
        self.assertEqual(task["qaTask"]["description"], qaTaskDescription)
        self.assertEqual(task["qaTask"]["dueDate"], qaTaskDueDate)

        for v in task.values():
            self.assertIsNotNone(v)
