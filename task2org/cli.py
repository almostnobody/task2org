"""Console script for task2org."""
import os
import sys
import click
import random
import time
import json
import re

from uuid import uuid1

# 12345678-1234-5678-1234-567812345678
# 296d835e-8f85-4224-8f36-c612cad1b9f8
# sys.exit()

# from taskw import TaskWarrior
import subprocess

# from PyOrgMode import PyOrgMode

from datetime import datetime, timedelta
import time
from tzlocal import get_localzone

local_tz = get_localzone()
delta = local_tz.utcoffset(datetime.now())
# print(delta)
# exit()
# item1 = "20170529T101500Z"
# item2 = "20170529T131500Z"
# item3 = "20170529T101500Z"
# print(item1)
# print(item2)
# item1 = local_tz.localize(datetime.strptime(item1, "%Y%m%dT%H%M%SZ"))
# item2 = datetime.strptime(item2, "%Y%m%dT%H%M%SZ")
# item3 = datetime.strptime(item3, "%Y%m%dT%H%M%SZ")
# print(item1)
# print(item2)
# print(item3)
# delta = local_tz.utcoffset(item2)
# item2 = local_tz.localize(item2 - delta)
# item3 = local_tz.localize(item3 - delta)
# print(item1)
# print(item2)
# print(item3)
# item1 = datetime.strftime(item1, "%Y%m%dT%H%M%SZ")
# item2 = datetime.strftime(item2, "%Y%m%dT%H%M%SZ")
# item3 = datetime.strftime(item3, "%Y%m%dT%H%M%SZ")
# print(item1)
# print(item2)
# print(item3)
# exit(0)


class Bunch:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)


def taskcompare(task1, task2, keys, comp):
    # keys.reverse()
    if len(keys) > 0:
        key = keys[0]
        c = lambda a, b: comp(a, b)
        if key.startswith("-"):
            key = key[1:]
            c = lambda a, b: not comp(a, b)
        keys = keys[1:]
        if task1 and task2:
            if task1[key] and task2[key] and comp(task1[key], task2[key]):
                return True
            elif task1[key]:
                return comp(1, 0)
            elif task2[key]:
                return comp(0, 1)
            else:
                if len(keys) > 0:
                    taskcompare(task1, task2, keys, comp)
        elif task1:
            return comp(1, 0)
        elif task2:
            return comp(0, 1)


class Task(dict):
    def __init__(self, d):
        self.tags = []
        self.depends = []
        for i in d.keys():
            self.__setitem__(i, d[i])
        if not self.project:
            self.project = "default"

    @property
    def done(self):
        if self.status == "completed":
            return True
        else:
            return False

    @property
    def waiting(self):
        if self.status == "waiting":
            return True
        else:
            return False

    @property
    def overdue(self):
        if self.due:
            return self.due > datetime.now(tz=local_tz)
        else:
            return False

    def create(self):
        self.uuid = str(uuid1())

    def __setitem__(self, key, item):
        if key != "description":
            try:
                item = local_tz.localize(datetime.strptime(item, "%Y%m%dT%H%M%SZ"))
            except:
                pass
            try:
                item = int(item)
            except:
                pass
        if key == "depends":
            if type(item) == type(""):
                item = item.split(",")
        self.__dict__[key] = item

    def __getitem__(self, key):
        if key in self.__dict__:
            item = self.__dict__[key]
        else:
            item = None
        return item

    def __getattr__(self, key):
        return self.__getitem__(key)

    def __todict__(self):
        d = {}
        for key in self.__dict__.keys():
            item = self.__dict__[key]
            if not key.startswith("_"):
                if type(item) == type(datetime.now(tz=local_tz)):
                    item = datetime.strftime(item, "%Y%m%dT%H%M%SZ")
                if key == "depends":
                    if len(item) > 0:
                        item = ",".join(item).replace(" ", "")
                    else:
                        item = None
                if key == "project" and item == "default":
                    item = None
                elif key == "id":
                    item = None
                if item:
                    d[key] = item
                elif type(item) == type(0):
                    d[key] = item
        return d

    def __repr__(self):
        return repr(self.__todict__())

    def __len__(self):
        return len(self.__dict__)

    def __delitem__(self, key):
        del self.__dict__[key]

    def clear(self):
        return self.__dict__.clear()

    def copy(self):
        return self.__dict__.copy()

    def has_key(self, k):
        return k in self.__dict__

    def update(self, *args, **kwargs):
        return self.__dict__.update(*args, **kwargs)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def pop(self, *args):
        return self.__dict__.pop(*args)

    def __cmp__(self, dict_):
        return self.__cmp__(self.__dict__, dict_)

    def __contains__(self, item):
        return item in self.__dict__

    def __iter__(self):
        return iter(self.__dict__)

    def __unicode__(self):
        return unicode(repr(self.__dict__))

    def __str__(self):
        return str(self.__dict__)

    def to_org(self, level=None):
        # * • [#A] Title :tag1:tag2:
        # DEADLINE: <2019-05-25 Sat 23:45> SCHEDULED: <2019-05-26 Sun 03:44 .+1w>
        # :PROPERTIES:
        # :property1: property value
        # :property2: property value
        # :END:
        def strf(dt):
            dt += delta
            return datetime.strftime(dt, "%Y-%m-%d %a %H:%M:%S")

        status = {"pending": "•", "completed": "DONE", "waiting": "WAITING"}
        priority = {"H": "A", "M": "B", "L": "C"}
        usedproperties = [
            "_level",
            "status",
            "priority",
            "description",
            "tags",
            "_closed",
            "_deadline",
            "_scheduled",
            "due",
            "note",
            "modified",
            "project",
            "id",
        ]
        lines = []
        l = []
        if level:
            l.append("*" * level)
        elif self._level:
            l.append("*" * self._level)
        else:
            l.append("*")
        l.append(status[self.status])
        if self.priority:
            priority = "[#" + priority[self.priority] + "]"
            l.append(priority)
        if self.description:
            l.append(self.description)
        if self.tags and len(self.tags) > 0:
            tags = ":" + ":".join(self.tags) + ":"
            l.append(tags)
        if len(l) > 0:
            lines.append(" ".join(l))
        l = []
        if self.status == "completed":
            s = "CLOSED: " + "[" + strf(self.modified) + "]"
            l.append(s)
        # if self.deadline:
        # s = "DEADLINE: " + "<" + strf(self.deadline) + ">"
        # l.append(s)
        if self.due:
            s = "SCHEDULED: " + "<" + strf(self.due) + ">"
            l.append(s)
        if len(l) > 0:
            lines.append(" ".join(l))
        l = []
        rep = self.__todict__()
        for k in rep.keys():
            # if k == "urgency":
            if k not in usedproperties:
                value = rep[k]
                if type(value) == type(list()) or type(value) == type(dict()):
                    value = json.dumps(value)
                l.append(":" + str(k) + ": " + str(value))
        if len(l) > 0:
            l = [":PROPERTIES:"] + l
            l.append(":END:")
            lines.append("\n".join(l))
        r = "\n".join(lines)
        if self.note:
            r = "\n\n".join([r, self.note])
        return r

    def __lt__(self, other):
        # For x < y
        comparekeys = ["waiting", "overdue", "due", "urgency", "done"]
        compare = lambda a, b: a < b
        return taskcompare(self, other, keys=comparekeys, comp=compare)

    def __gt__(self, other):
        # For x > y
        comparekeys = ["waiting", "overdue", "due", "urgency", "done"]
        compare = lambda a, b: a > b
        return taskcompare(self, other, keys=comparekeys, comp=compare)

    def __eq__(self, other):
        # For x == y
        comparekeys = ["uuid"]
        compare = lambda a, b: a == b
        return taskcompare(self, other, keys=comparekeys, comp=compare)

    def __le__(self, other):
        # For x <= y
        comparekeys = ["waiting", "overdue", "due", "urgency", "done"]
        compare = lambda a, b: a <= b
        return taskcompare(self, other, keys=comparekeys, comp=compare)

    def __ge__(self, other):
        # For x >= y
        comparekeys = ["waiting", "overdue", "due", "urgency", "done"]
        compare = lambda a, b: a >= b
        return taskcompare(self, other, keys=comparekeys, comp=compare)

    def __ne__(self, other):
        # For x != y OR x <> y
        # comparekeys = ["uuid", "due", "urgency", "done"]
        # comparekeys = ["uuid", "overdue", "due", "urgency", "done"]
        comparekeys = solf.keys()
        compare = lambda a, b: a != b
        return taskcompare(self, other, keys=comparekeys, comp=compare)


class OrgDocument:
    def __init__(self, name):
        self.file = name
        r, ext = os.path.splitext(name)
        _, project = os.path.split(r)
        self.project = project
        if not os.path.exists(name):
            # with open(name, "w") as f:
                # f.write("")
            self.text = ""
            mtime = datetime.now(tz=local_tz).timestamp()
        else:
            with open(name, "r") as f:
                self.text = f.read()
            mtime = os.path.getmtime(name)
        # self.mtime = mtime
        mtime = datetime.fromtimestamp(mtime)
        mtime = local_tz.localize(mtime) - delta
        # print()
        # print(mtime)
        # print(mtime - delta)
        # print(mtime + delta)
        # print()
        self.mtime = mtime
        self.byuuid = {}
        tasks = []
        # task = None
        text = None
        note = []
        for block in self.text.split("\n\n"):
            if block.startswith("*"):
                if text:
                    note = "\n".join(note)
                    task = OrgTask(
                        text, note=note, modified=mtime, project=self.project
                    )
                    note = []
                    if not task.uuid:
                        print("task without uuid")
                        print(task)
                        print()
                    tasks.append(task)
                # сразу создавать OrgTask
                # task = Bunch()
                text = block
            else:
                note.append(block)
            # print("startblock")
            # print(block)
            # print("endblock")
        if text:
            note = "\n".join(note)
            task = OrgTask(text, note=note, modified=mtime, project=self.project)
            tasks.append(task)

        self.tasks = []
        parents = []
        i = 0
        lastlevel = 1
        while i < len(tasks):
            # print(tasks[i].text)
            # task = OrgTask(
            # tasks[i].text, note=tasks[i].note, modified=mtime, project=self.project
            # )
            task = tasks[i]
            if not task.uuid:
                task.create()
            if task._level > lastlevel:
                parents.append(i - 1)
            elif task._level < lastlevel:
                if len(parents) > 0:
                    parents.pop()
            if task._level == 1:
                parents = []
            if len(parents) > 0:
                p = tasks[parents[-1]]
                if task.uuid not in p.depends:
                    p.depends.append(task.uuid)
                    p.modified = task.modified
                    tasks[parents[-1]] = p
                    self.byuuid[p.uuid] = p

            self.byuuid[task.uuid] = task
            if task._level == 1:
                self.tasks.append(task.uuid)
            lastlevel = task._level
            i += 1

    def save(self, test=False):
        def get_items(uuids, level=1, used=[], mtime=None):
            items = []
            for u in uuids:
                # try:
                if u in self.byuuid:
                    task = self.byuuid[u]
                    if mtime and task.modified and task.modified > mtime:
                        mtime = task.modified
                    depends = []
                    if task.depends:
                        for uuid in task.depends:
                            if uuid in self.byuuid:
                                depends.append(uuid)
                        try:
                            depends = sorted(
                                depends, key=lambda uuid: self.byuuid[uuid]
                            )
                        except:
                            pass
                    children, l, m = get_items(
                        depends, level=level + 1, used=used, mtime=mtime
                    )
                    if mtime and m and m > mtime:
                        mtime = m
                    for us in l:
                        if us not in used:
                            used.append(us)
                    add = False
                    if task.done:
                        if len(children) > 0:
                            add = True
                        elif level == 1 and (
                            task.modified
                            > datetime.now(tz=local_tz) - timedelta(hours=1)
                        ):
                            add = True
                        elif level > 1 and (
                            task.modified
                            > datetime.now(tz=local_tz) - timedelta(days=1)
                        ):
                            add = True
                    elif task.waiting:
                        # if level > 1:
                        if level > 1 and (
                            (
                                task.modified
                                > datetime.now(tz=local_tz) - timedelta(days=1)
                            )
                            or (
                                task.wait
                                and (
                                    abs(task.wait - datetime.now(tz=local_tz))
                                    < timedelta(hours=5)
                                )
                            )
                        ):
                            add = True
                        # elif len(children) > 0:
                        # add = True
                        # print(task.description)
                        # print(level)
                        # print(len(children))
                        # print()
                        # print("\n\n".join(children).replace("\n", "\n\t"))
                        else:
                            add = False
                        if (
                            level == 1
                            and task.wait
                            and (
                                abs(task.wait - datetime.now(tz=local_tz))
                                < timedelta(hours=3)
                            )
                        ):
                            add = True
                    else:
                        add = True
                    if add:
                        if task.uuid not in used:
                            used.append(task.uuid)
                            items.append(task.to_org(level=level))
                            items += children
                # except Exception as e:
                # print(u == e)
                # pass
                # print(self.byuuid)
                # print(uuid)
            return items, used, mtime

        # mtime = datetime.fromtimestamp(self.mtime)
        mtime = self.mtime
        items, used, mtime = get_items(self.tasks, mtime=mtime)
        text = "\n\n".join(items)
        if text == self.text:
            pass
            # print(self.project + " input == output")
        else:
            print(self.file)
            print(self.project + " input != output")
            if not test:
                with open(self.file, "w") as f:
                    f.write(text)
                stinfo = os.stat(self.file)
                # print()
                # oldmtime = self.mtime
                # print(mtime)
                # print(oldmtime)
                # print(mtime - oldmtime)
                # print(self.file)
                # print()
                if mtime == self.mtime:
                    mtime += timedelta(seconds=1)
                mtime = time.mktime(mtime.timetuple())
                os.utime(self.file, (stinfo.st_atime, mtime))


# * • [#A] Title :tag1:tag2:
# DEADLINE: <2019-05-25 Sat 23:45> SCHEDULED: <2019-05-26 Sun 03:44 .+1w>
# :PROPERTIES:
# :property1: property value
# :property2: property value
# :END:


class OrgTask(Task):
    def __init__(
        self, string=None, note=None, modified=None, project="default", task=None
    ):
        self.project = project
        self.depends = []
        if modified:
            if type(modified) != type(datetime.now(tz=local_tz)):
                modified = datetime.fromtimestamp(modified)
                modified = local_tz.localize(modified - delta)
            self.modified = modified
        # else:
        # modified = datetime.now(tz=local_tz)
        if note:
            self.note = note
        if task:
            for k in task:
                self[k] = task[k]
        if string:
            lines = string.split("\n")
            self.__firstline__(lines[0])
            if len(lines) > 1:
                properties = []
                prop = False
                for line in lines[1:]:
                    if line == (":PROPERTIES:"):
                        prop = True
                    if not prop:
                        self.__secondline__(line)
                    if line == (":END:"):
                        prop = False
                    if prop:
                        properties.append(line)
                self.__properties__(properties)

    def parsetime(string):
        if string.startswith("[") or string.startswith("<"):
            string = string[1:-1]
        string = string.split(" ")
        date = string[0]
        if len(string) > 2:
            time = string[2]
            ending = time.split("-")
            if len(ending) > 1:
                dt = " ".join([date, ending[0]])
            else:
                dt = " ".join([date, time])
        else:
            dt = " ".join([date, "00:00"])
        if len(string) > 3:
            rep = string[3]
        try:
            dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        except:
            dt = datetime.strptime(dt, "%Y-%m-%d %H:%M")
        dt = local_tz.localize(dt - delta)
        return dt

    def __firstline__(self, string):
        # * • [#A] Title :tag1:tag2:
        items = string.split(" ")
        level = len(items[0])
        status = items[1]
        priority = items[2]
        tags = items[-1]
        if not (priority.startswith("[") and priority.endswith("]")):
            priority = None
        else:
            priority = priority[2:-1]
        if not (tags.startswith(":") and tags.endswith(":")):
            tags = []
        else:
            tags = tags[1:-1].split(":")
        if priority:
            start = 3
        else:
            start = 2
        if tags:
            end = -1
        else:
            end = None
        title = " ".join(items[start:end])
        self._level = level
        statuses = {"•": "pending", "DONE": "completed", "WAITING": "waiting"}
        if status and status in statuses:
            self.status = statuses[status]
        else:
            self.status = "pending"
        priorities = {"A": "H", "B": "M", "C": "L"}
        if priority:
            self.priority = priorities[priority]
        self.description = title
        self.tags = tags

    def __secondline__(self, string):
        # DEADLINE: <2019-05-25 Sat 23:45> SCHEDULED: <2019-05-26 Sun 03:44 .+1w>
        # CLOSED: [2021-04-29 Thu 15:06] DEADLINE: <2021-04-29 Thu 14:42 -1d> SCHEDULED: <2021-04-29 Thu 14:42-15:00>

        sp = string.split(": ")
        types = []
        values = []
        for s in sp:
            items = s.split(" ")
            word = items[-1]
            if re.match("^[A-Z]+$", word):
                types.append(word)
                if len(items) > 1:
                    values.append(" ".join(items[:-1]))
            else:
                values.append(s)
        i = 0
        while i < len(types):
            t = types[i]
            v = values[i]
            i += 1
            # if t == "DEADLINE":
            # self.deadline = OrgTask.parsetime(v)
            if t == "SCHEDULED":
                self.due = OrgTask.parsetime(v)
            if t == "CLOSED":
                self.modified = OrgTask.parsetime(v)

    def __properties__(self, strings):
        # :PROPERTIES:
        # :property1: property value
        # :property2: property value
        # :END:
        for string in strings:
            string = string.split(": ")
            name = string[0][1:]
            value = " ".join(string[1:])
            if not name in ["PROPERTIES:", "END:", "LAST_REPEAT"]:
                # print(name)
                # print(value)
                if name == "CREATED":
                    self.entry = OrgTask.parsetime(str(value).strip()[1:-1])
                elif str(value).startswith("[") and str(value).endswith("]"):
                    # # self[name] = str(value)[1:-1].split(", ")
                    # print(value)
                    print(name)
                    print(value)
                    self[name] = json.loads(str(value).replace('" "', '" : "'))
                else:
                    self[name] = str(value).strip()

    # def to_tw(self):
    # # сделать экспорт и импорт в таскварриор и сделать сравнения, создание если новое и тп
    # usedproperties = [
    # "level",
    # "status",
    # "priority",
    # "title",
    # "tags",
    # "closed",
    # "deadline",
    # "scheduled",
    # "modified",
    # "depends",
    # "project",
    # ]
    # status = {"•": "pending", "DONE": "completed", "WAITING": "waiting"}
    # priority = {"A": "H", "B": "M", "C": "L"}
    # dt = {}
    # dt["status"] = status[self.status]
    # if self.priority:
    # dt["priority"] = priority[self.priority]
    # dt["description"] = self.title
    # task = Task(dt)
    # task.due = self.scheduled
    # task.modified = self.modified
    # if self.uuid:
    # task.uuid = self.uuid
    # task.depends = self.depends
    # task.tags = self.tags
    # for k in self.keys():
    # if k not in usedproperties:
    # task[k] = self[k]
    # return task

    def taskto_org(self):
        ot = OrgTask()
        status = {"pending": "•", "completed": "DONE", "waiting": "WAITING"}
        priority = {"H": "A", "M": "B", "L": "C"}
        usedproperties = [
            "status",
            "priority",
            "description",
            "tags",
            "due",
            "wait",
            "modified",
            "depends",
        ]
        ot["status"] = status[self.status]
        if self.priority:
            ot["priority"] = priority[self.priority]
        ot.title = self.description
        ot.scheduled = self.due
        ot.modified = self.modified
        ot.uuid = self.uuid
        if self.depends:
            ot.depends = self.depends
        ot.tags = self.tags
        for k in self.keys():
            if k not in usedproperties:
                ot[k] = self[k]
        return ot


# class TaskTree(object):
# class Node(object):
# def __init__(self, uuid, children=[]):
# self.uuid = uuid
# self.children = children

# def __init__(self, skipwaiting=True):
# self.__byuuid__ = {}
# self.__list__ = []
# self.__children__ = []
# self.skipwaiting = skipwaiting

# def buildnode(self, task):
# node = Node(task.uuid)
# for t in task.depends:
# node.children.append(self.buildnode(self.__byuuid__[t]))

# def buildtree(self):
# for uuid in self.__byuuid__:
# if uuid not in self.__children__:
# node = Node(uuid, self.__byuuid__[uuid].depends)
# self.__list__.append(node)

# def __setitem__(self, uuid, task):
# self.__byuuid__[uuid] = task
# if task.depends:
# self.__children__ += task.depends

# def __getitem__(self, key):
# if key in self.__dict__:
# item = self.__dict__[key]
# else:
# item = None
# return item

# def __getattr__(self, key):
# return self.__getitem__(key)


@click.group()
@click.option("--orgdir", required=True, help="directory with org files")
@click.option("-w", "--showwaiting", is_flag=True, help="show waiting status")
@click.pass_context
def main(ctx, orgdir, showwaiting):
    statuses = ["pending"]
    if showwaiting:
        statuses.append("waiting")
    if not ctx.obj:
        ctx.obj = Bunch()
    # ctx.obj.w = TaskWarrior()
    ctx.obj.orgdir = orgdir
    # tasks = ctx.obj.w.load_tasks()

    tasks = subprocess.getoutput(
        ["task status:pending or status:waiting or status:completed export"]
    )
    tasks = json.loads(tasks)
    # pending = tasks["pending"]
    # completed = tasks["completed"]
    # children = []
    byuuid = {}
    # twprojects = {}

    # for t in pending + completed:
    for t in tasks:
        task = Task(t)
        byuuid[task.uuid] = task
        # if task.depends:
        # for uuid in task.depends:
        # children.append(uuid)
        # project = task.project
        # if project not in twprojects.keys():
        # twprojects[project] = {}
    # ctx.obj.twprojects = twprojects
    # ctx.obj.children = children
    ctx.obj.byuuid = byuuid

    # новый алгоритм:
    # - делаем отдельный byuuid для orgdir
    # - сравниваем два byuuid
    # - каждый файл орг перемещается орг.сейв и удаляется после записи новой версии
    # - итоговый byuiid импортируетс в тасквариор, а потом заного экспортируется в новый byuuid и собирается в файлы orgdir
    orgprojects = {}
    for root, dirs, files in os.walk(orgdir):
        for file in files:
            file = os.path.join(root, file)
            if re.search(r".*\(conflict.*", file):
                os.remove(file)
                continue
            r, ext = os.path.splitext(file)
            r, name = os.path.split(r)
            # print(file)
            if ext == ".org":
                document = OrgDocument(file)
                orgprojects[name] = document

    ctx.obj.orgprojects = orgprojects


@main.command()
@click.option("-t", "--test", is_flag=True)
@click.pass_context
def sync(ctx, test):
    orgprojects = ctx.obj.orgprojects
    # twprojects = ctx.obj.twprojects
    # children = ctx.obj.children
    byuuid = ctx.obj.byuuid
    synced = []
    children = []
    print("syncing")
    newbyuuid = {}
    for project in orgprojects:
        document = orgprojects[project]
        for uuid in document.byuuid:
            orgtask = document.byuuid[uuid]
            task = orgtask
            if uuid in byuuid.keys():
                twtask = byuuid[uuid]
                if orgtask._new:
                    task = orgtask
                elif orgtask.modified and twtask.modified:
                    if orgtask.modified > twtask.modified:
                        # if twtask.id in [3, 10, 32]:
                        if False:
                            # if twtask.uuid == "a08f1583-1bb6-4ad5-865a-250e93b97164":
                            print()
                            print("org modified")
                            print(orgtask.description)
                            print(orgtask.modified)
                            print(twtask.modified)
                            print(twtask.id)
                            print()
                        task = orgtask
                    else:
                        # if twtask.id in [3, 10, 32]:
                        if False:
                            # if twtask.uuid == "a08f1583-1bb6-4ad5-865a-250e93b97164":
                            print()
                            print("tw modified")
                            print(orgtask.description)
                            print(orgtask.modified)
                            print(twtask.modified)
                            print(twtask.id)
                            print()
                        task = twtask
                else:
                    task = twtask
                newbyuuid[uuid] = task
            else:
                newbyuuid[uuid] = task
            if task.depends and len(task.depends) > 0:
                children += task.depends
    for uuid in byuuid:
        if uuid not in newbyuuid:
            newbyuuid[uuid] = byuuid[uuid]

    projects = {}
    for uuid in newbyuuid:
        task = newbyuuid[uuid]
        project = task.project
        if project not in projects:
            # print(project)
            projects[project] = []
        if uuid not in children:
            projects[task.project].append(task.uuid)

    for project in projects:
        path = os.path.join(ctx.obj.orgdir, project + ".org")
        tasks = projects[project]
        tasks = sorted(tasks, key=lambda uuid: newbyuuid[uuid])
        existed = os.path.exists(path)
        # with open(path, "w") as f:
        # f.write("")
        # for t in tasks:
            # print(t)
        orgd = OrgDocument(path)
        orgd.byuuid = newbyuuid
        orgd.tasks = tasks
        if not test:
            orgd.save()
    updatetasks = []
    for uuid in newbyuuid:
        task = newbyuuid[uuid]
        # try:
        # task.create()
        # except Exception as e:
        # print(e)
        # print(task.__repr__())
        # print(json.dumps([task.__repr__()]))
        # print(task.uuid)
        if task.modified > datetime.now(tz=local_tz) - timedelta(days=30):
            updatetasks.append(task.__todict__())
        # updatetasks.append(json.dumps(newbyuuid[uuid].__todict__()))
        # updatetasks.append(newbyuuid[uuid].__repr__())
    # print(json.dumps(updatetasks))
    if test:
        print("wait to import")
        time.sleep(10)
    print("started import")
    sp = subprocess.run(
        ["task", "import"],
        # stdin=self.__repr__(),
        input=json.dumps(updatetasks),
        capture_output=True,
        text=True,
        # check=True,
    )
    print("finished import")



if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
