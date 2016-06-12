#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from alli_systemdata  import load_alliance_config


alli_sysconfig = load_alliance_config()


def get_all_alliance_level():
    return alli_sysconfig.get('guild_level', {}).keys()

def get_alliance_level_conf(level):
    _conf = alli_sysconfig.get('guild_level', {})
    return _conf.get(level, {})

def get_alliance_contribution_conf(contribute_id):
    _conf = alli_sysconfig.get('guild_contribution', {})
    return _conf.get(contribute_id, {})

def get_vip_conf(vip_level):
    _conf = alli_sysconfig.get('vip', {})
    return _conf.get(vip_level, {})

def get_sacrifice_award_conf(sacrifice_level):
    _conf = alli_sysconfig.get('guild_sacrifice', {})
    return _conf.get(sacrifice_level, {})

def get_shop_limit_conf(guild_level):
    _conf = alli_sysconfig.get('guild_shop_limit', {})
    return _conf.get(guild_level, {})

def get_shop_item_conf(shop_item_id):
    _conf = alli_sysconfig.get('guild_shop_item', {})
    return _conf.get(shop_item_id, {})







