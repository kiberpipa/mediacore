#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

from fabric.api import env, run, local, put, sudo
from fabric.operations import prompt
from fabric.context_managers import cd
from fabric.contrib.files import upload_template, exists
from fabric.contrib.project import rsync_project

from ielectric.fab import *


env.here = os.path.dirname(os.path.abspath(__file__))

env.hosts = ['dogbert.kiberpipa.org']
env.user = 'arhivar'
env.project_name = 'mediacore'
env.location = '/srv/video.kiberpipa.org/'
env.use_buildout = True
