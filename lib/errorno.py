#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2012 Don.Li
# Summary: 


NO_ERROR           = 0
UNKNOWN_ERROR      = 1

LOGIN_NO_CHARACTER = 2
LOGIN_UNKNOWN_CID  = 3
LOGIN_PARAMS_ERR   = 4
SESSION_NOT_VALID  = 5
NET_ERROR          = 6
LOGIN_REPEAT_NAME  = 7  # 玩家昵称重复
SERVER_IS_CLOSED   = 8  # 服务器已关闭
CHAR_IN_FORBIDDEN  = 9  # 被封号中
CHAR_IN_MUTE       = 10 # 被禁言中

CLIENT_VERSION_ERROR  = 11 # 客户端版本号异常

#SERVER_NOT_EXIST         = 10 
#SERVER_VERSION_NOT_EXIST = 11 
#SERVER_STATE_ERROR       = 12 
#SERVER_VERSION_DISCARD   = 13 
#SERVER_SYS_ERR           = 14 

CHAR_DATA_ERROR     = 13 # 玩家数据异常, 请重新登陆
CONNECTION_LOSE     = 14 # 已失去连接, 请重新登陆
RECONNECT_FAIL      = 15 # 重连失败
NOT_FOUND_CONF      = 16 # 缺少配置
CLIENT_DATA_ERROR   = 17 # 客户端参数格式错误
REPEAT_REWARD_ERROR = 18 # 不能重复领取奖励
REQUEST_LIMIT_ERROR = 19 # 条件不满足
BUY_MAX_NUM_ERROR   = 20 # 购买次数已达上限, 无法购买
HAVE_NUM_TO_USE     = 21 # 当前剩余次数未用完, 无法购买
CHAR_NOT_ONLINE     = 22 # 玩家不在线
UNKNOWN_CHAR        = 23 # 未知玩家
NO_REWARD_ERROR     = 24 # 没有奖励可领取

REGISTER_REQUEST_REPEAT = 25 # 玩家重复的注册请求
REGISTER_FAIL_ERROR     = 26 # 玩家注册失败, 请稍后重试

CHAR_HONOR_NOT_ENOUGH      = 39 # 荣誉不足
CHAR_CREDIT_NOT_ENOUGH     = 40 # 点卷不足
CHAR_ITEM_NOT_ENOUGH       = 41 # 道具不足
CHAR_GOLD_NOT_ENOUGH       = 42 # 金币不足
CHAR_SOUL_NOT_ENOUGH       = 43 # 仙魂不足
CHAR_LEVEL_LIMIT           = 44 # 玩家等级限制
CHAR_HUNYU_NOT_ENOUGH      = 45 # 玉魄不足
CHAR_PRESTIGE_NOT_ENOUGH   = 46 # 声望不足
CHAR_DOUZHAN_NOT_ENOUGH    = 47 # 斗战不足
CHAR_TUTORIAL_FINISHED     = 48 # 新手引导步骤已完成
CHAR_VIP_LEVEL_LIMIT       = 49 # 玩家VIP等级限制

ITEM_TYPE_ERROR            = 50 # 道具类型不匹配
UNKNOWN_ITEM_ERROR         = 51 # 未知道具
UNKNOWN_FELLOW_ERROR       = 52 # 未知伙伴
FELLOW_DECOMPOSITION_ERROR   = 53 # 已上阵或已进阶的伙伴不可炼化, 要先重生
EQUIP_DECOMPOSITION_ERROR    = 54 # 已穿戴或已洗炼的装备不可炼化, 要先重生
TREASURE_DECOMPOSITION_ERROR = 55 # 已穿戴或已精炼的宝物不可炼化, 要先重生
UNKNOWN_EQUIP_ERROR          = 56 # 未知装备
UNKNOWN_TREASURE_ERROR       = 57 # 未知宝物
FELLOW_REBORN_ERROR          = 58 # 已上阵或未进阶的伙伴不可重生
EQUIP_REBORN_ERROR           = 59 # 已穿戴或未洗炼的装备不可重生
ITEM_USER_ERROR              = 60 # 道具不能使用
TREASURE_REBORN_ERROR        = 61 # 已穿戴或未精炼的宝物不可重生
REFRESH_MYSTICAL_SHOP_LIMIT  = 62 # 神秘商店免费刷新次数已用完
AWARD_TIME_EXPIRE            = 63 # 领奖中心奖励已过期
ARENA_IN_REWARD_TIME         = 64 # 结算时间为每天22:00-22:15, 期间不能战斗
NO_PACKAGE_REWARD            = 65 # 无礼包奖励可领取
EAT_PEACH_ERROR              = 66 # 当前时间点没有桃可吃
NO_MONTHLY_CARD_ERROR        = 67 # 尚未购买月卡
MONTHLY_CARD_REWARD_ERROR    = 68 # 月卡奖励今日的已领取
PAY_LOGIN_COST_NOT_ENOUGH    = 69 # 豪华签到充值金额不足, 无法签到
PAY_LOGIN_REWARD_HAD_GOT     = 70 # 今日的豪华签到奖励已领取

#RANDCARD_INVALID_REQ =70
RANDCARD_NO_POOL_CFG         = 71
RANDCARD_TYPE_ERROR          = 72 # 抽卡类型异常
IN_COOLDOWN_ERROR            = 73 # 冷却时间还未结束
SHOP_ITEM_MAX_NUM            = 74 # 商城道具的购买次数限制
ARENA_EXCHANGE_MAX_NUM       = 75 # 竞技场 声望兑换次数限制
IN_CLIMBING_MAX_LAYER        = 76 # 天外天 当前在可扫荡的最高层 不能扫荡
IN_CLIMBING_MIN_LAYER        = 77 # 天外天 已经在第一层 不能重置
IN_CLIMBING_ONGOING          = 78 # 天外天 扫荡中, 无法重置
IN_CLIMBING_DONE             = 79 # 天外天 没有正在进行的扫荡事件
IN_PLUNDER_ONGOING           = 80 # 拥有当前宝物碎片的玩家正在被抢夺
UNKNOWN_TREASURESHARD        = 81 # 宝物碎片数量已发生变化


#FELLOW_SET_FORMATION_INVALID_REQ      = 80
#FELLOW_SET_FORMATION_IS_NOT_MY_FELLOW = 81
#FELLOW_SET_FORMATION_DUPLICATE        = 82
FELLOW_NOT_ENOUGH             = 82 # 伙伴数量不足
FELLOW_MAJOR_REPLACE_ERROR    = 83 # 主角不可被替换
FELLOW_COMMON_ON_TROOP        = 84 # 相同的伙伴不能同时上阵
DUNGEON_CHALLENGE_COUNT_LIMIT = 85 # 副本挑战次数限制
SCENE_CHALLENGE_COUNT_LIMIT   = 86 # 今日挑战次数已用完
ACTIVE_FIGHT_TIME_ERROR       = 87 # 活动副本未开启
SCENE_STAR_NOT_ENOUGH         = 88 # 不是满星副本, 不能扫荡
SCENE_NEED_PASSED             = 89 # 与精英副本关联的剧情副本未通关, 不能战斗

GROWTH_PLAN_BUY_LIMIT         = 90 # VIP等级不足, VIP2及以上才可购买
GROWTH_PLAN_BUYED             = 91 # 成长计划已购买
GROWTH_PLAN_REWARD_ERROR      = 92 # 购买成长计划后才可领取
GROWTH_PLAN_LEVEL_LIMIT       = 93 # 玩家等级达到后才可领取
STRING_LENGTH_ERROR             = 94 # 字符长度超出限制

PREP_ELITESCENE_NEED_WIN      = 95 # 前一个精英副本需要战斗胜利后才能挑战当前副本
SCENE_CHALLENGE_NEED_WIN      = 96 # 剧情副本 需要挑战成功才能领取奖励
SCENE_RESET_ERROR             = 97 # 剧情副本 重置挑战次数失败


LEVEL_UPGRADE_TARGET_INVALID  = 100 # 目标不能升级
# 好友 邮件
USER_HAD_YOUR_FRIEND          = 101 # 对方已经是您的好友了
INVITE_FRIEND_REPEAT          = 102 # 您已向此玩家提出了好友邀请, 请耐心等待
UNKNOWN_MAIL_REQUEST          = 103 # 未知邮件异常
DOUZHAN_MAX_ERROR             = 104 # 斗战点已达最大值
DOUZHAN_DAILY_ERROR           = 105 # 今日可领取斗战点次数已用完
FRIENDS_COUNT_SELF_ERROR      = 106 # 您的好友数量已达到上限
FRIENDS_COUNT_OTHER_ERROR     = 107 # 对方好友数量已达到上限
USER_HAS_NOT_YOUR_FRIEND      = 109 # 对方不是您的好友

FELLOW_CAPACITY_NOT_ENOUGH    = 108 # 伙伴背包容量不足
ADVANCED_MAX_COUNT = 110 # 进阶等级已达到上限

ITEM_CAPACITY_NOT_ENOUGH          = 111 # 道具背包容量不足
EQUIP_CAPACITY_NOT_ENOUGH         = 112 # 装备背包容量不足
TREASURE_CAPACITY_NOT_ENOUGH      = 113 # 宝物背包容量不足
EQUIPSHARD_CAPACITY_NOT_ENOUGH    = 114 # 装备碎片背包容量不足

CONSTELLATION_REWARD_RECEIVED = 121 # 奖励已领取
CONSTELLATION_SELECT_REACH_MAX = 122 # 已達當日觀星上限
CONSTELLATION_NEED_REFRESH     = 123 # 数据已更新, 请刷新页面。未领奖励已发放到领奖中心
CONSTELLATION_STAR_SYNC_ERROR  = 124 # 可点击的星星数据和服务器不同步

ALLIANCE_NAME_DUPLICATED     = 130 # 仙盟名重复
ALLIANCE_APPLY_COUNT_ERROR   = 131 # 已达到可申请加入的仙盟个数
ALLIANCE_UNKNOWN_ERROR       = 132 # 仙盟不存在
ALLIANCE_AUTHORITY_ERROR     = 133 # 无权限进行此操作
ALLIANCE_OTHER_HAD_IN        = 134 # 提示对方已经在仙盟中了
ALLIANCE_MEMBERS_MAX_ERROR   = 135 # 仙盟已满员
ALLIANCE_LEADER_LEAVE_ERROR  = 136 # 会长不能离开仙盟
ALLIANCE_VICE_LIMIT_ERROR    = 137 # 副会长人数已达上限
ALLIANCE_DISSOLVE_ERROR      = 138 # 还有仙盟成员 不能解散仙盟
ALLIANCE_NOT_MEMBER_ERROR    = 139 # 该玩家不是本仙盟成员

EXCHANGE_NOT_FOUND = 140 #免费兑换ID未找到

LIMIT_FELLOW_NO_ERROR        = 141 # 当前没有限时神将活动
LIMIT_FELLOW_FREE_ERROR      = 142 # 限时神将免费抽卡的时间没到
ATLASLIST_AWARD_HAD_ERROR    = 143 # 图鉴的奖励已领取

GOODWILL_LEVEL_MAX_ERROR     = 144 # 神将的好感度等级已经是最高等级
GOODWILL_ITEM_ERROR          = 145 # 缺少好感度道具
AWARD_HAD_IN_AWARD_CENTER    = 146 # 奖励已经发放到领奖中心

ALLIANCE_NOT_IN              = 147 # 玩家没有仙盟
ALLIANCE_LEVEL_MAX           = 148 # 等级已经是最高等级了
ALLIANCE_MESSAGES_MAX_ERROR  = 149 # 公会留言板 今日留言次数已用尽


# code in 150 - 160 used to oss gift code feature
GIFT_CODE_FAILURE            = 151 # 兑换失败
GIFT_CODE_OVERDUE            = 154 # 兑换码已过期

ALLIANCE_HAD_HALL_CONTRIBUTE = 161 # 今日已完成大殿建设
SACRIFICE_ALLIANCE_COUNT_ERROR  = 162 # 仙盟女蜗宫贡献总次数限制
SACRIFICE_NORMAL_COUNT_ERROR    = 163 # 仙盟女蜗宫个人贡献拜祭次数限制
SACRIFICE_CREDITS_COUNT_ERROR   = 164 # 仙盟女蜗宫个人钻石拜祭次数限制
ALLIANCE_CONTRIBUTE_NOT_ENOUGH  = 165 # 仙盟总贡献度不足
MEMBER_CONTRIBUTE_NOT_ENOUGH    = 166 # 个人可用贡献度不足
EXCHANGE_ITEM_COUNT_NOT_ENOUGH  = 167 # 仙盟商店中道具已无兑换次数
EXCHANGE_ITEM_REPEAT_ERROR      = 168 # 只能兑换一次
REFRESH_ITEM_ERROR              = 169 # 请刷新道具商店
ALLIANCE_LEVEL_LIMIT            = 170 # 仙盟等级限制
ALLIANCE_REQUEST_UNKNOWN        = 171 # 未知入会申请
ALLIANCE_HAD_IN_POSITION        = 172 # 任命前后玩家职位无变化
ALLIANCE_SELF_HAD_IN            = 173 # 提示自己已经在仙盟中了
ALLIANCE_NEED_LEADER            = 174 # 只有仙盟盟主才能进行此操作
ALLIANCE_NEED_VICE_LEADER       = 175 # 职位为副盟主或盟主才能进行此操作

# 每日任务
DAILY_QUEST_SCORE_NOT_ENOUGH    = 181 # 每日任务积分不足, 不能领取奖励
UNKNOWN_DAILY_QUEST_ID          = 182 # 未知每日任务ID
EXCITE_ACTIVITY_STOP_ERROR      = 183 # 精彩活动已关闭

#World BOSS
WORLDBOSS_NOT_RUNNING = 190 #不在活动时间段内
WORLDBOSS_CD          = 191 #CD时间未到
WORLDBOSS_INSPIRE_MAX_LEVEL_REACHED = 192 #已到达最大鼓舞等级
WORLDBOSS_NO_INSPIRE_CONFIG = 193 #无此鼓舞等级配置
WORLDBOSS_DEAD_ALREADY      = 194 #Boss已死

# joust
JOUST_HAD_END_ERROR              = 201 # 活动已结束，下周一再加油吧
JOUST_PERIOD_OF_TIME_ERROR       = 202 # 只有8:00-23:00可以进行比拼
JOUST_BATTLE_COUNT_NOT_ENOUGH    = 203 # 今日挑战次数已用完，请购买或等待明天
JOUST_BUY_COUNT_LIMIT_ERROR      = 204 # 今天购买次数已经用完
JOUST_EXCHANGE_COUNT_ERROR       = 205 # 兑换次数已用完
JOUST_FREE_COUNT_ERROR           = 206 # 免费挑战剩余次数大于0时不能购买

#新年红包
NEWYEAR_PACKAGE_RECEIVED_ALREADY = 211 #今天的礼包已领取

#一键转化
NO_ANY_GREEN_FELLOW  = 220 #玩家一个绿色伙伴也没有

#背包出售
ITEM_CANNOT_SELL     = 230 #物品没有出售价格，不能出售
UNKNOWN_BAG_TYPE     = 231 #未知背包类型或该背包不能出售物品

#皇陵探宝
HAD_DIG_MAX_COUNT    = 232 #已经达到最大次数或钻石不足

# 玉魄
JADE_RANDOM_TEN_ERROR    = 241 # 需要主角50级或VIP5级才可使用
JADE_UPGRADE_LEVEL_ERROR = 242 # 你的鉴玉等级不需要提升
UNKNOWN_JADE_ERROR       = 243 # 未知玉魄
JADE_CAPACITY_NOT_ENOUGH = 244 # 玉魄背包容量不足

# 幸运抽奖
LUCKY_TURNTABLE_REPEAT_ERROR = 246 # 今日的幸运次数已使用
UNKNOWN_TURNTABLE_TYPE_ERROR = 247 # 未知转盘档位
TURNTABLE_PAY_NOT_ENOUGH     = 248 # 充值金额不足, 无法抽奖

#限时商店
TIME_LIMITED_SHOP_ALL_GROUP_CLOSED     = 250 #所有组都已关闭
TIME_LIMITED_SHOP_CURRENT_GROUP_CLOSED = 251 #当前组没有开始
TIME_LIMITED_SHOP_CANNOT_BUY           = 252 #不能购买，已达购买上限
TIME_LIMITED_SHOP_NO_SUCH_ITEM         = 253 #无此商品

#团购礼包
GROUP_BUY_MAX_COUNT         = 254  # 团购购买次数上限
BUY_NUM_NOT_ENOUGH          = 255  # 团购人数不够
BUY_STATUS_IS_WRONG         = 256  # 未购买该团购礼包
BUY_GROUP_TYPE_WRONG        = 257  # 团购档次或人数错误

#成长计划
GROW_PLAN_GOT               = 258  # 成长计划已经领取过

# 阵营抽卡
CAMP_RANDCARD_MAX_LIMIT     = 261  # 抽卡次数已达最大次数
CAMP_RANDCARD_ID_ERROR      = 262  # 抽卡阵营信息已更新

NO_MONTHLY_CARD_REWARD_ERROR  = 263 # 没有月卡奖励可领取

#开服活动
OPEN_SERVER_KIND_WRONG      = 264  #开服活动购买领取类型错误
OPEN_SERVER_IS_CLOSED       = 265  #开服活动已经关闭
OPEN_SERVER_SHOP_HAD_BUY    = 266  #开服商店已经买过了
OPEN_SERVER_QUEST_WRONG     = 267  #开服活动任务未完成
OPEN_SERVER_QUEST_IS_NOT_EXISTED = 268 #开服活动任务不存在
UNKNOWN_OPEN_SERVER_QUEST_ID = 269 #开服活动任务id未知
OPEN_SERVER_SHOP_NUM_MAX    = 270  #开服活动商店购买已达最大
OLD_SERVER_HAS_NOT_ACTIVITY = 271  #老服没有此活动

#成就
UNKNOWN_ACHIEVEMENT_TYPE = 272  #没有此成就类型
ACHIEVEMENT_HAS_NOT_FINISH = 273 #成就未完成
PREVIOUS_ACHIEVEMENT_NOT_FINISH = 274 #前置成就未完成

#新跑马灯
MSG_TYPE_WRONG = 275 #跑马灯类型错误
BROAD_MSG_OUT_DATE = 276 #已过期
REWARD_IS_NOT_ENOUGH = 277 #红包已经领完了

#改名卡
NICK_NAME_IS_USED = 278  #名字已被占用
NAMED_TYPE_IS_WRONG = 279 #修改类型错误 

# 神秘商店消耗道具/钻石刷新次数
REFRESH_MYSTICAL_SHOP_MAX_COUNT = 281 # 神秘商店每日刷新次数已用完


# OSS GM error
OSS_EXCITE_ACTIVITY_ERROR   = 10022 # OSS同步精彩活动配置错误
OSS_LIMIT_FELLOW_ERROR      = 10024 # OSS同步限时神将配置错误, 同时有多个限时神将被开启
OSS_TIME_LIMITED_SHOP_GROUP_EXCEPTION = 10026 #配置限时商店商品组时出错
OSS_TIME_LIMITED_SHOP_ITEM_EXCEPTION  = 10027 #配置限时商店商品时出错

OSS_ACTIVITY_NOTICE_ERROR             = 10031 # OSS同步活动公告配置错误

OSS_ACTIVITY_LOTTERY_ERROR            = 10033 # OSS 同步活动翻牌配置错误

OSS_ACTIVITY_RANDOM_PACKAGE_ERROR     = 10034 # OSS 同步随机礼包配置错误

OSS_ACTIVE_MONSTER_DROP_ERROR         = 10035 # OSS 同步活动怪物掉落错误

OSS_PAY_ACTIVITY_GROUP_ERROR          = 10036 # OSS 同步充值分组配置错误
OSS_PAY_ACTIVITY_CONF_ERROR           = 10037 # OSS 同步充值详细配置错误

OSS_CONSUME_ACTIVITY_CONF_ERROR       = 10038 # OSS 同步消费详细配置错误
OSS_CONSUME_ACTIVITY_GROUP_ERROR      = 10039 # OSS 同步消费分组配置错误

OSS_ACTIVITY_ID_WRONG                 = 10040 # OSS 活动id必须大于0
OSS_ACTIVITY_GROUP_OPEN_WRONG         = 10041 # OSS 活动激活的组超过了一个。

OSS_ITEM_TYPE_IS_WRONG                = 10042 # OSS 未知道具类型
OSS_PACKAGE_TYPE_ERROR                = 10043 # OSS 未知礼包类型

OSS_EXCITE_ACTIVITY_IS_CLOSED         = 10044 # 精彩活动未关闭
