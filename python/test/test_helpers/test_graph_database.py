#!/usr/bin/env python
# -*- coding: utf-8 -*-

from py2neo.ogm import GraphObject, Property, RelatedFrom, RelatedTo


TESTGRAPHDB = {
    'bolt': True,
    'host': 'localhost',
    'bolt_port': 7687,
    'user': 'neo4j',
    'password': 'test'
}


class Project(GraphObject):
    __primarykey__ = "ID"

    name = Property()
    sourcerank = Property()
    versions_count = Property()


class Contributor(GraphObject):
    __primarykey__ = "uuid"

    name = Property()
    github_id = Property()
    login = Property()

    projects = RelatedTo("Project", "CONTRIBUTES_TO")


class Language(GraphObject):
    __primarykey__ = "name"

    projects = RelatedFrom("Project", "IS_WRITTEN_IN")