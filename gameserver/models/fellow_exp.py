#!/usr/bin/env python
# -*- coding: utf-8 -*-

from twisted.internet import defer
from protocol_manager import cs_call
from time import time

from log import log
from errorno import *
from constant import *

from manager.gsattribute import GSAttribute

from system import sysconfig

class FellowExp(object):
    def __init__(self):
        pass #We may put some optimize data here

    def getFellowSacrificeExp( self, fellow_id, level_cur, exp_cur ): #Return: int
        dic_fellow_cfg = sysconfig['fellow']
        fellow_cfg = None
        if fellow_id not in dic_fellow_cfg:
            log.debug('Can not find fellow cfg of ', fellow_id)
            return -1
        else:
            fellow_cfg = dic_fellow_cfg[fellow_id]

        log.debug('[ getFellowSacrificeExp ] fellow_cfg:', fellow_cfg)
        quality = fellow_cfg['Quality']
        exp_base = fellow_cfg['Exp']
        level_born = fellow_cfg['Level']

        level_born_exp = self.getFellowTotalExpToLevel(fellow_id, level_born)
        level_cur_exp   = self.getFellowTotalExpToLevel(fellow_id, level_cur)
        level_delta_exp = 0
        if level_cur_exp >= level_born_exp:
            level_delta_exp = level_cur_exp - level_born_exp
        else:
            log.warn('Exp3930527 Cur level is small than born level! fellow id {0}, lvl-born_exp {1}, lvl-cur-exp {2}'.format( fellow_id, level_born_exp, level_cur_exp ))

        log.debug('[ getFellowSacrificeExp ], fellow_id {0},  {1} + {2} + {3}'.format( fellow_id, exp_base, level_delta_exp, exp_cur ))
        return exp_base + level_delta_exp + exp_cur

    def handleFellowLevelUp( self, fellow_id, level, exp, level_up_limit ): #Return: final_level:int, final_exp:int
        log.debug('[ handleFellowLevelUp ] FellowLevelUp, fellow_id {0}, lvl {1}, exp {2}, lvl-limist {3}'.format( fellow_id, level, exp, level_up_limit ))
        dic_fellow_cfg = sysconfig['fellow']
        fellow_cfg = None
        if fellow_id not in dic_fellow_cfg:
            log.debug('[ handleFellowLevelUp ] Can not find fellow cfg of ', fellow_id)
            return -1
        else:
            fellow_cfg = dic_fellow_cfg[fellow_id]
        role_list_lvl_exp_step, dic__fellow_list_lvl_exp_step, role_list_lvl_exp, dic__fellow_list_lvl_exp = sysconfig['roleexp']

        quality = fellow_cfg['Quality']

        if quality not in dic__fellow_list_lvl_exp_step:
            log.error('[ handleFellowLevelUp ] Invalid quality {0}, fellow id {1}'.format( quality, fellow_id ))
            return 0, 0

        list_lvl_exp_step = dic__fellow_list_lvl_exp_step[quality]

        final_level = level
        final_exp = exp
        MAX_LEVEL = 60
        for lvl in range(level, MAX_LEVEL):
            if lvl >= level_up_limit:
                log.debug('[ handleFellowLevelUp ] Get level up limit! fellow id {0}, lvl {1}, lvl-limit {2}'.format( fellow_id, lvl, level_up_limit ))
                break;

            step_exp = list_lvl_exp_step[lvl]
            if final_exp >= step_exp:
                final_level = lvl+1
                final_exp -= step_exp
            else:
                break
        return final_level, final_exp

    def getFellowLevelUpExp( self, fellow_id, level_cur ): #Return: exp:int
        dic_fellow_cfg = sysconfig['fellow']
        fellow_cfg = None
        if fellow_id not in dic_fellow_cfg:
            log.debug('Can not find fellow cfg of ', fellow_id)
            return -1
        else:
            fellow_cfg = dic_fellow_cfg[fellow_id]

        quality = fellow_cfg['Quality']
        role_list_lvl_exp_step, dic__fellow_list_lvl_exp_step, role_list_lvl_exp, dic__fellow_list_lvl_exp = sysconfig['roleexp']
        if quality < CARD_COLOR_WHITE or quality > CARD_COLOR_ORANGE:
            log.error('Invalid quality {0}, fellow id {1}'.format( quality, fellow_id ))
            return -1
        if quality not in dic__fellow_list_lvl_exp_step:
            log.error('Can not find quality {0} in cfg, fellow id {1}'.format( quality, fellow_id ))
            return -1

        list_lvl_exp = dic__fellow_list_lvl_exp[quality]
        if level_cur < 0 or level_cur >= len(list_lvl_exp):
            log.error('Exp4505938 Invalid level ', level_cur)
            return -1

        return list_lvl_exp[level_cur]

    def getFellowTotalExpToLevel( self, fellow_id, level ): #Return: exp:int
        dic_fellow_cfg = sysconfig['fellow']
        fellow_cfg = None
        if fellow_id not in dic_fellow_cfg:
            log.debug('Can not find fellow cfg of ', fellow_id)
            return -1
        else:
            fellow_cfg = dic_fellow_cfg[fellow_id]

        quality = fellow_cfg['Quality']
        role_list_lvl_exp_step, dic__fellow_list_lvl_exp_step, role_list_lvl_exp, dic__fellow_list_lvl_exp = sysconfig['roleexp']
        if quality < CARD_COLOR_WHITE or quality > CARD_COLOR_ORANGE:
            log.error('Invalid quality {0}, fellow id {1}'.format( quality, fellow_id ))
            return -1
        if quality not in dic__fellow_list_lvl_exp:
            log.error('Can not find quality {0} in cfg, fellow id {1}'.format( quality, fellow_id ))
            return -1

        list_lvl_exp = dic__fellow_list_lvl_exp[quality]
        return list_lvl_exp[level]

    def getFellowLevelByTotalExp( self, fellow_id, exp ): #Return: int
        log.debug('getFellowLevelByTotalExp, fellow_id {0}, exp {1}'.format( fellow_id, exp ))
        dic_fellow_cfg = sysconfig['fellow']
        fellow_cfg = None
        if fellow_id not in dic_fellow_cfg:
            log.debug('Can not find fellow cfg of ', fellow_id)
            return -1
        else:
            fellow_cfg = dic_fellow_cfg[fellow_id]

        log.debug('[ getFellowLevelByTotalExp ] fellow_cfg:', fellow_cfg)
        quality = fellow_cfg['Quality']
        role_list_lvl_exp_step, dic__fellow_list_lvl_exp_step, role_list_lvl_exp, dic__fellow_list_lvl_exp = sysconfig['roleexp']
        if quality < CARD_COLOR_WHITE or quality > CARD_COLOR_ORANGE:
            return -1

        list_lvl_exp = dic__fellow_list_lvl_exp[quality]
        
        left = 0
        right = len(list_lvl_exp) - 1
        log.debug('****** Start search, left {0}, right {1}, list-lvl-exp:{2}'.format( left, right, list_lvl_exp ))
        while(True):
            if left > right:
                log.error('Exp3092843 left > right!')
                break
            if right - left < 2:
                break

            mid = (left + right) / 2
            exp_mid = list_lvl_exp[mid]
            log.debug('****** Left {0}, right {1}. Sel mid {2}, exp {3}'.format( left, right, mid, exp_mid ))
            if exp < exp_mid:
                right = mid
            else:
                left = mid
        log.debug('****** Finish search, left {0}, right {1}'.format( left, right ))
        return left

    def getCharacterTotalExpToLevel( self, target_level ):#Return: int
        role_list_lvl_exp_step, dic__fellow_list_lvl_exp_step, role_list_lvl_exp, dic__fellow_list_lvl_exp = sysconfig['roleexp']
        need_exp = 0
        for lvl in range(1, target_level):
            if lvl >= 0 and lvl < len(role_list_lvl_exp):
                need_exp += role_list_lvl_exp[lvl]
            else:
                log.error('Can not find exp cfg of level ', lvl)
        return need_exp

g_FellowExp = FellowExp()   