from api.tests.util import TestBase


class TestTasks(TestBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

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

    def testDeleteTask(self):
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

        deleteTaskResponse = self.client.delete(
            f"/tasks/{task['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(deleteTaskResponse.status_code, 200)

        getTaskResponse = self.client.get(
            f"/tasks/{task['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(getTaskResponse.status_code, 404)
