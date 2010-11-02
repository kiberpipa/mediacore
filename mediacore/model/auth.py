import os
from datetime import datetime

from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Unicode, Integer, DateTime
from sqlalchemy.orm import backref, mapper, relation, synonym

from mediacore.model.meta import DBSession, metadata
from mediacore.lib.compat import sha1
from mediacore.plugin import events

users = Table('users', metadata,
    Column('user_id', Integer, autoincrement=True, primary_key=True),
    Column('user_name', Unicode(16), unique=True, nullable=False),
    Column('email_address', Unicode(255), unique=True, nullable=False),
    Column('display_name', Unicode(255)),
    Column('password', Unicode(80)),
    Column('created', DateTime, default=datetime.now),
    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

users_groups = Table('users_groups', metadata,
    Column('user_id', Integer, ForeignKey('users.user_id',
        onupdate="CASCADE", ondelete="CASCADE")),
    Column('group_id', Integer, ForeignKey('groups.group_id',
        onupdate="CASCADE", ondelete="CASCADE")),
    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

groups = Table('groups', metadata,
    Column('group_id', Integer, autoincrement=True, primary_key=True),
    Column('group_name', Unicode(16), unique=True, nullable=False),
    Column('display_name', Unicode(255)),
    Column('created', DateTime, default=datetime.now),
    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

groups_permissions = Table('groups_permissions', metadata,
    Column('group_id', Integer, ForeignKey('groups.group_id',
        onupdate="CASCADE", ondelete="CASCADE")),
    Column('permission_id', Integer, ForeignKey('permissions.permission_id',
        onupdate="CASCADE", ondelete="CASCADE")),
    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

permissions = Table('permissions', metadata,
    Column('permission_id', Integer, autoincrement=True, primary_key=True),
    Column('permission_name', Unicode(16), unique=True, nullable=False),
    Column('description', Unicode(255)),
    mysql_engine='InnoDB',
    mysql_charset='utf8',
)


class User(object):
    """
    Basic User definition
    """
    query = DBSession.query_property()

    def __repr__(self):
        return '<User: email="%s", display name="%s">' % (
                self.email_address, self.display_name)

    def __unicode__(self):
        return self.display_name or self.user_name

    @property
    def permissions(self):
        perms = set()
        for g in self.groups:
            perms = perms | set(g.permissions)
        return perms

    @classmethod
    def by_email_address(cls, email):
        # TODO: Move this function to User.query
        return DBSession.query(cls).filter(cls.email_address==email).first()

    @classmethod
    def by_user_name(cls, username):
        # TODO: Move this function to User.query
        return DBSession.query(cls).filter(cls.user_name==username).first()

    def _set_password(self, password):
        """Hash password on the fly."""
        hashed_password = password

        if isinstance(password, unicode):
            password_8bit = password.encode('UTF-8')
        else:
            password_8bit = password

        salt = sha1()
        salt.update(os.urandom(60))
        hash = sha1()
        hash.update(password_8bit + salt.hexdigest())
        hashed_password = salt.hexdigest() + hash.hexdigest()

        # make sure the hased password is an UTF-8 object at the end of the
        # process because SQLAlchemy _wants_ a unicode object for Unicode columns
        if not isinstance(hashed_password, unicode):
            hashed_password = hashed_password.decode('UTF-8')
        self._password = hashed_password

    def _get_password(self):
        return self._password

    password = property(_get_password, _set_password)

    def validate_password(self, password):
        """Check the password against existing credentials.

        :param password: the password that was provided by the user to
            try and authenticate. This is the clear text version that we will
            need to match against the hashed one in the database.
        :type password: unicode object.
        :return: Whether the password is valid.
        :rtype: bool

        """
        hashed_pass = sha1()
        hashed_pass.update(password + self.password[:40])
        return self.password[40:] == hashed_pass.hexdigest()

class Group(object):
    """
    An ultra-simple group definition.
    """
    def __repr__(self):
        return '<Group: name=%s>' % self.group_name

    def __unicode__(self):
        return self.group_name

class Permission(object):
    """
    A relationship that determines what each Group can do
    """
    def __unicode__(self):
        return self.permission_name


mapper(
    User, users,
    extension=events.MapperObserver(events.User),
    properties={
        'password': synonym('_password', map_column=True),
    },
)

mapper(
    Group, groups,
    properties={
        'users': relation(User, secondary=users_groups, backref='groups'),
    },
)

mapper(
    Permission, permissions,
    properties={
        'groups': relation(Group,
            secondary=groups_permissions,
            backref='permissions',
        ),
    },
)
