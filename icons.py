#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 25 14:47:10 2018

@author: adam
"""

from PyQt5.QtGui import QIcon

from . import icons_res
import qtawesome as qta
from PyQt5.QtGui import  QColor

_app_icon_color=QColor.fromRgbF(213/255.,43/255.,30/255.,1)
_icons = {
    #'app' : QIcon(":/images/icons/cadquery_logo_dark.svg")
    'app' : qta.icon('mdi6.atom-variant', color=_app_icon_color)
    }


_icons_specs = {
    'new'  : (('fa.file-o',),{}),
    'hide'  : (('mdi6.eye-check',),{}),
    'import'  : (('mdi.application-import',),{}),
    'export'  : (('mdi.application-export',),{}),
    'db-config'  : (('mdi6.database-cog',),{}),
    'db-plus'  : (('mdi.database-plus',),{}),
    'db'  : (('mdi.database',),{}),
    'open' : (('fa.folder-open-o',),{}),
    # borrowed from spider-ide
    'autoreload': [('fa.repeat', 'fa.clock-o'), {'options': [{'scale_factor': 0.75, 'offset': (-0.1, -0.1)}, {'scale_factor': 0.5, 'offset': (0.25, 0.25)}]}],
    'save' : (('fa.save',),{}),
    'save_as': (('fa.save','fa.pencil'),
               {'options':[{'scale_factor': 1,},
                           {'scale_factor': 0.8,
                            'offset': (0.2, 0.2)}]}),
    'run'  : (('fa.play',),{}),
    'delete' : (('fa.trash',),{}),
    'delete-many' : (('fa.trash','fa.trash',),
                     {'options' : \
                      [{'scale_factor': 0.8,
                         'offset': (0.2, 0.2),
                         'color': 'gray'},
                       {'scale_factor': 0.8}]}),
    'help' : (('fa.life-ring',),{}),
    'about': (('fa.info',),{}),
    'preferences' : (('fa.cogs',),{}),
    'inspect' : (('fa.cubes','fa.search'),
                 {'options' : \
                  [{'scale_factor': 0.8,
                     'offset': (0,0),
                     'color': 'gray'},{}]}),
    'screenshot' : (('fa.camera',),{}),
    'screenshot-save' : (('fa.save','fa.camera'),
                         {'options' : \
                          [{'scale_factor': 0.8},
                           {'scale_factor': 0.8,
                            'offset': (.2,.2)}]})
}

def icon(name):

    if name in _icons:
        return _icons[name]

    args,kwargs = _icons_specs[name]

    return qta.icon(*args,**kwargs)