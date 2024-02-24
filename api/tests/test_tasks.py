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

        cls.testTask = {
            "name": "test",
            "description": "test",
            "dueDate": "2022-01-01T00:00:00",
            "qaTask": {
                "name": "qatest",
                "description": "qatest",
                "dueDate": "2022-01-01T00:00:00",
            },
        }

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

        taskResponse = self.createTask(
            user,
            project["id"],
            milestone["id"],
            **self.testTask,
        )

        self.assertEqual(taskResponse.status_code, 200)

        task = taskResponse.json()

        self.assertEqual(task["projectId"], project["id"])
        self.assertEqual(task["milestoneId"], milestone["id"])
        self.assertEqual(task["name"], self.testTask["name"])
        self.assertEqual(task["description"], self.testTask["description"])
        self.assertEqual(task["dueDate"], self.testTask["dueDate"])
        self.assertEqual(task["qaTask"]["name"], self.testTask["qaTask"]["name"])
        self.assertEqual(
            task["qaTask"]["description"], self.testTask["qaTask"]["description"]
        )
        self.assertEqual(task["qaTask"]["dueDate"], self.testTask["qaTask"]["dueDate"])

        for v in task.values():
            self.assertIsNotNone(v)

    def testGetTask(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()
        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        createTaskResponse = self.createTask(
            user,
            project["id"],
            milestone["id"],
            **self.testTask,
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
        self.assertEqual(task["name"], self.testTask["name"])
        self.assertEqual(task["description"], self.testTask["description"])
        self.assertEqual(task["dueDate"], self.testTask["dueDate"])
        self.assertEqual(task["qaTask"]["name"], self.testTask["qaTask"]["name"])
        self.assertEqual(
            task["qaTask"]["description"], self.testTask["qaTask"]["description"]
        )
        self.assertEqual(task["qaTask"]["dueDate"], self.testTask["qaTask"]["dueDate"])

        for v in task.values():
            self.assertIsNotNone(v)

    def testUpdateTask(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()
        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        task = self.createTask(
            user,
            project["id"],
            milestone["id"],
            **self.testTask,
        )

        self.assertEqual(task.status_code, 200)

        task = task.json()

        updateTask = {
            "name": "updated",
            "description": "updated",
            "dueDate": "2022-01-01T00:00:00",
            "priority": "High",
            "qaTask": {
                "name": "updated",
                "description": "updated",
                "dueDate": "2022-01-01T00:00:00",
                "status": "In Progress",
            },
        }

        updateTaskResponse = self.client.patch(
            f"/tasks/{task['id']}",
            json=updateTask,
            headers=self.userToHeader(user),
        )

        self.assertEqual(updateTaskResponse.status_code, 200)

        task = updateTaskResponse.json()

        self.assertEqual(task["projectId"], project["id"])
        self.assertEqual(task["milestoneId"], milestone["id"])
        self.assertEqual(task["name"], updateTask["name"])
        self.assertEqual(task["description"], updateTask["description"])
        self.assertEqual(task["dueDate"], updateTask["dueDate"])
        self.assertEqual(task["priority"], updateTask["priority"])
        self.assertEqual(task["qaTask"]["name"], updateTask["qaTask"]["name"])
        self.assertEqual(
            task["qaTask"]["description"], updateTask["qaTask"]["description"]
        )
        self.assertEqual(task["qaTask"]["dueDate"], updateTask["qaTask"]["dueDate"])
        self.assertEqual(task["qaTask"]["status"], updateTask["qaTask"]["status"])

        for v in task.values():
            self.assertIsNotNone(v)

    def testUpdateTaskProjectAndMilestone(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        task = self.createTask(
            user,
            project["id"],
            milestone["id"],
            **self.testTask,
        )

        self.assertEqual(task.status_code, 200)

        task = task.json()

        newProject = self.createProject(user, "test", "test").json()
        newMilestone = self.createMilestone(
            user, newProject["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        updateTask = {
            "projectId": newProject["id"],
            "milestoneId": newMilestone["id"],
        }

        updateTaskResponse = self.client.patch(
            f"/tasks/{task['id']}",
            json=updateTask,
            headers=self.userToHeader(user),
        )

        self.assertEqual(updateTaskResponse.status_code, 200)

        task = updateTaskResponse.json()

        self.assertEqual(task["projectId"], newProject["id"])
        self.assertEqual(task["milestoneId"], newMilestone["id"])
