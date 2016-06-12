#-*-coding: utf-8-*-
# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2012 Don.Li
# Summary: 

CS_USER_TOTSEC   = 600
GS_USER_TOTSEC   = 550
GATE_USER_TOTSEC = 400

MAX_SYNC_CNT_PER_LOOP = 1000
SYNC_CS_INTERVAL      = 5
SYNC_DB_INTERVAL      = 2
SYNC_ALLIANCE_INTERVAL = 20

PLATFORM_ID = ['', 'tipcat', 'pp']

# table list of no delete field.
TABLEs_NO_DELETED = 'character', 'scene', 'elitescene', 'activescene', 'climbing_tower', 'atlaslist', 'goodwill'

MAX_SYNC_CS_CNT_PER_LOOP = 100

SESSIONKEY_TIMEOUT = 30
SESSION_LOGOUT_REAL = 300  # client logout timeout 5min

#gm user id
SET_GM_USER = 'SET_GM_USER'

GAME_REGION_CP_CODE = 'pp'
GAME_REGION_ID   = 51
GAME_REGION_VER  = 1.0
GAME_REGION_SN   = '123321'
ROBOT_COUNT = 5000

GAME_REGION_SEQ = 0 
GAME_REGION_NAME = ''

FOR_ALL         = 0
FOR_SERVER_ONLY = 1
FOR_CLIENT_ONLY = 2

TIPCAT_GAME_ID = '3d3k' 
TIPCAT_LOGIN_URLBASE = 'http://login.5xhb.com/openid/openid_session_check'
TIPCAT_LOGIN_SECURITY_ID = '8thke4b385gh76sj2df8'

HEITAO_LOGIN_URLBASE     = 'http://smi.heitao.com/sgxyj/auth'
RESOURCE_ANDROIS_URLBASE = 'http://sg.pic.heitao.com/android/res'


# oss of local url and online url
TIPCAT_LOCAL_OSS_URLBASE  = 'http://192.168.8.189/west_api/game_api/gift_code_use'
TIPCAT_ONLINE_OSS_URLBASE = 'http://api.test.3dk.tjsanguo.com/game_api/gift_code_use'
TIPCAT_OSS_SECURITY_ID    = '92a549dd5a3301'

# oss of web session
TIPCAT_WEB_SESSION_ID     = 'w2LKSDjjlsdli99uoj#@#'
HEITAO_WEB_SESSION_ID     = 'Sd(-@FqMOTZBf'

HEITAO_PAYMENT_SUCC      = 1 # 支付成功
HEITAO_PAYMENT_FAIL      = 2 # 支付失败

TIPCAT_CID = 1  # TipCat
HEITAO_CID = 2  # heitao
#LOGIN_CID_ALL = [TIPCAT_CID]

CARD_SHRINE_GREEN    = 1
CARD_SHRINE_BLUE     = 2
CARD_SHRINE_PURPLE   = 3

CARD_COLOR_WHITE  = 0
CARD_COLOR_GREEN  = 1
CARD_COLOR_BLUE   = 2
CARD_COLOR_PURPLE = 3
CARD_COLOR_ORANGE = 4
CARD_COLOR_COUNT  = 5

DICT_ACCOUNT_REGISTERED  = 'DICT_ACCOUNT_REGISTERED'
DICT_NICKNAME_REGISTERED = 'DICT_NICKNAME_REGISTERED'
SET_CID_REGISTERED       = 'SET_CID_REGISTERED'
DICT_SHRINE_STATUS      = 'DICT_SHRINE_STATUS_%s'

#CHARACTER_DEFAULT_GOLDS     =5000000
#CHARACTER_DEFAULT_CREDITS   =500
#CHARACTER_DEFAULT_SOUL      =990000
#CHARACTER_DEFAULT_ENERGY    =30

FELLOWS_PER_PAGE = 500
FELLOW_DEFAULT_CAPACITY = 100
FELLOW_FORMATION_CAPACITY = 6

FELLOW_DEFAULT_LEVEL = 1
FELLOW_DEFAULT_EXP = 0
FELLOW_DEFAULT_QUALITY_LEVEL = 0


SCENE_USER_COUNT = 5 # 主场景内可显示的玩家个数

FELLOW_GUARD_INFO = 'FELLOW_GUARD_INFO'
FELLOW_TOWN_ADV_LIST        = 'FELLOW_TOWN_ADV_LIST'       #field: cid,  value: [ town_id, ... ]
FELLOW_TOWN_ADV_HISTORY = 'FELLOW_TOWN_ADV_HISTORY_%s'  #field: cid,  value: dumps data of TownAdventureHistory

DUNGEON_STAR = [1, 2, 3]

FELLOWS_LIMIT_WITH_PLAYER_LEVEL = 2, 6, 12, 17, 24, 25, 35, 40, 50, 60, 70 #2, 5, 12, 16, 22, 30, 35, 40, 45, 50, 55

# 玉魄上阵的玩家等级限制
JADE_LIMIT_WITH_PLAYER_LEVEL = 30, 35, 40, 45, 50, 55, 60, 65

FELLOW_LEVELUP_LIMIT   = 100
FELLOW_FORMATION_ORDER = (1, 4, 2, 3, 5, 0) # fellow阵型的优先级顺序

#BAG_NORMAL_DEFAULT_CAPACITY = 65535
BAG_MAX_PILE = 99

MONSTER_DROP_HISTORY     = 'MONSTER_DROP_HISTORY_%s'
BATTLE_MONSTER_EXP_RATIO = 10
MAX_SKILL_BALL_INDEX     = 12 # 玩家技能栏的技能球最大数
UNLOCK_TYPE_ITEM         = 1 # 解锁方式之使用道具
UNLOCK_TYPE_CREDITS      = 2 # 解锁方式之直接购买

FELLOW_QUALITY = ['White', 'Green', 'Blue', 'Purple', 'Orange', 'Red', 'RoleExp'] # 依次为白品,绿品,蓝品,紫品,橙品,红品,主角, 下标依次为0,1,2,3,4,5,6
QUALITY_WHITE  = 0
QUALITY_GREEN  = 1
QUALITY_BLUE   = 2
QUALITY_PURPLE = 3

STRENGTHEN_NORMAL = 1 # 强化方式之 普通强化
STRENGTHEN_AUTO   = 2 # 强化方式之 自动强化

ITEM_STRENGTHEN_COST = ['WhiteCost', 'GreenCost', 'BlueCost', 'PurpleCost', 'OrangeCost'] # 依次为白品,绿品,蓝品,紫品,橙品, 下标依次为0,1,2,3,4

TREASURE_STRENGTHEN_QUALITYLEVEL_MAX = 7 # 宝物强化时 品级(QualityLevel)大于7的不添加 
TREASURE_REFINE_QUALITYLEVEL_MAX     = 7 # 宝物精炼时 品级(QualityLevel)小于等于7的不可精炼
TREASURE_STRENGTHEN_EXP_TO_GOLDS     = 15 # 宝物强化时消耗金币和获取经验之间的折算倍数

# 背包容量: 0-None, 1-装备, 2-装备碎片, 3-伙伴背包, 4-分魂背包, 5-道具背包, 6-宝物背包, 7-玉魄背包
BAG_TYPE_CAPACITY    = ['', 'equip_capacity', 'equipshard_capacity', 'fellow_capacity', 'fellowsoul_capacity', 'item_capacity', 'treasure_capacity', 'jade_capacity']
BAG_DEFAULT_CAPACITY = [0, 30, 50, 100, 65535, 30, 30, 150]   # 背包初始容量值

BAG_EQUIP         = [2, 3, 4, 5]     # 装备背包
BAG_TREASURE      = [6, 7]           # 宝物背包
BAG_ITEM          = [8, 15, 16, 17, 19, 20]  # 道具背包
BAG_EQUIPSHARD    = [9]              # 装备碎片背包
BAG_FELLOWSOUL    = [10]             # 分魂背包
BAG_TREASURESHARD = [12, 13]         # 宝物碎片背包
BAG_FELLOW        = [14]             # 伙伴背包
BAG_JADE          = [11]             # 玉魄背包

ITEM_TYPE_MONEY        = 1  # 货币
ITEM_TYPE_NECKLACE     = 2  # necklace
ITEM_TYPE_ARMOR        = 3  # 护甲
ITEM_TYPE_HELMET       = 4  # 头盔
ITEM_TYPE_WEAPON       = 5  # 武器
ITEM_TYPE_HORSE        = 6  # 宝马
ITEM_TYPE_BOOKWAR      = 7  # 兵书
ITEM_TYPE_ITEM         = 8  # 普通道具
ITEM_TYPE_EQUIPSHARD   = 9  # 装备碎片
ITEM_TYPE_FELLOWSOUL   = 10 # 分魂
ITEM_TYPE_JADE         = 11 # 玉魄
ITEM_TYPE_HORSESHARD   = 12 # 宝马碎片
ITEM_TYPE_BOOKWARSHARD = 13 # 兵书碎片
ITEM_TYPE_FELLOW       = 14 # 伙伴
ITEM_TYPE_CHEST        = 15 # 宝箱
ITEM_TYPE_PACKAGE      = 16 # 礼包
ITEM_TYPE_GOODWILL     = 17 # 好感度礼物
ITEM_TYPE_KEY          = 19 # 打开宝箱的钥匙
ITEM_TYPE_DIRECT_PACKAGE = 20 # 定向礼包

ITEM_AVOID_WAR_ID      = 101 #免战牌道具ID
ITEM_SCENE_RESET_ID    = 801 # 重置副本怪物组次数道具ID
ITEM_SCENE_SWEEP_ID    = 802 # 扫荡副本的道具ID
ITEM_GUANXINGLING      = 901 #观星令道具ID
ITEM_JADE_UPGRADE_ID   = 902 # 提示当前鉴玉等级到指定等级

ITEM_REFINE_STONE   = 501 # 洗炼石 用于装备洗炼
ITEM_REFRESH_SHOP   = 201 # 刷新令 用于神秘商店
ITEM_MONEY_GOLDS    = 1   # 金币
ITEM_MONEY_CREDITS  = 2   # 钻石
ITEM_MONEY_ENERGY   = 3   # 精力
ITEM_MONEY_SOUL     = 4   # 仙魂
ITEM_MONEY_HUNYU    = 5   # 魂玉
ITEM_MONEY_PRESTIGE = 6   # 声望
ITEM_MONEY_HONOR    = 7   # 荣誉
ITEM_MONEY_DOUZHAN  = 8   # 斗战
ITEM_GUILD_CONTRIBUTE  = 9  # 仙盟建设度
ITEM_MEMBER_CONTRIBUTE = 10 # 仙盟个人贡献
ITEM_REFINE_STONE   = 501 # 洗炼石 用于装备洗炼
ITEM_REFRESH_SHOP   = 201 # 刷新令 用于神秘商店
ITEM_RANDCARD_GREEN = 301 # 情缘符 用于抽绿卡

ATTRIBUTE_TYPE_HORSE_EXP   = 100 # 坐骑经验
ATTRIBUTE_TYPE_BOOKWAR_EXP = 101 # 兵书经验
ATTRIBUTE_TYPE_GOODWILL    = 102 # 好感度
ATTRIBUTE_TYPE_DOUZHAN     = 103 # 斗战点上限
ATTRIBUTE_TYPE_JADE_EXP    = 104 # 玉魄经验

EXP_HORSE_ID   = 32999 # 经验马
EXP_BOOKWAR_ID = 52999 # 经验书
EXP_GOLD_HORSE_ID   = 33999 # 经验金马
EXP_GOLD_BOOKWAR_ID = 53999 # 经验金书

RESOURCE_PACKAGE_ID = 9999 # 第一次下载资源包时可获得的礼包ID

# 竞技场、夺宝每次斗战点消耗
PVP_NEED_DOUZHAN = 2

MYSTICAL_REFRESH_COST       = 20 # 神秘商店刷新1次消耗的钻石数
# 神秘商店刷新方式
MYSTICAL_REFRESH_FREE       = 1  # 使用免费次数刷新
MYSTICAL_REFRESH_ITEM       = 2  # 使用刷新令道具
MYSTICAL_REFRESH_CREDITS    = 3  # 使用钻石刷新

GROWTH_PLAN_PRICE  = 1000 # 成长计划价格


LUCKY_RANKLIST               = 'LUCKY_RANKLIST' # arena lucky ranklist key
AWARD_ID                     = 'AWARD_ID'       # 领奖中心的primary award id

HASH_ITEM_SHOP_RECORD        = 'HASH_ITEM_SHOP_RECORD'
HASH_VIP_LEVELUP_RECORD      = 'HASH_VIP_LEVELUP_RECORD_%s'
HASH_CAMP_PREDESTINE         = 'HASH_CAMP_PREDESTINE'
HASH_CHARACTER_CAMP          = 'HASH_CHARACTER_CAMP'
HASH_TREASURE_CHARACTER_CAMP = 'HASH_TREASURE_CHARACTER_CAMP'
HASH_TREASURE_CHARACTER_IDS  = 'HASH_TREASURE_CHARACTER_IDS'

HASH_FINISHED_DIALOGUE_GROUP = 'HASH_FINISHED_DIALOGUE_GROUP'
HASH_DUNGEON_DROP_RATE       = 'HASH_DUNGEON_DROP_RATE_%s'
HASH_SCENE_STAR_REWARDED     = 'HASH_SCENE_STAR_REWARDED'
HASH_SCENE_COOLDOWN_TIME     = 'HASH_SCENE_COOLDOWN_TIME'
SET_SCENE_CID_STAR           = 'SET_SCENE_CID_STAR'
HASH_SCENE_RESET_DAILY       = 'HASH_SCENE_RESET_DAILY'

# 精英副本
HASH_ELITESCENE_PASSED       = 'HASH_ELITESCENE_PASSED'

# 天外天
SET_CLIMBING_CID_LAYER       = 'SET_CLIMBING_CID_LAYER'

# 竞技场
HASH_ARENA_EXCHANGE          = 'HASH_ARENA_EXCHANGE'
HASH_ARENA_RANK              = 'HASH_ARENA_RANK'
SET_ARENA_CID_RANK           = 'SET_ARENA_CID_RANK' # sorted set
HASH_ARENA_LUCKY_RANKLIST    = 'HASH_ARENA_LUCKY_RANKLIST'
HASH_ACTIVITY_LOTTERY        = 'HASH_ACTIVITY_LOTTERY'
HASH_MYSTICAL_SHOP           = 'HASH_MYSTICAL_SHOP'
HASH_MYSTICAL_LOTTERY        = 'HASH_MYSTICAL_LOTTERY'
HASH_AWARD_CENTER            = 'HASH_AWARD_CENTER_%s'
HASH_HINCRBY_KEY             = 'HASH_HINCRBY_KEY'

# 抽卡池的神坛信息
HASH_SHRINE_TYPE             = 'HASH_SHRINE_TYPE_%s'
# 阵营抽卡
HASH_CAMPRAND_COMMON         = 'HASH_CAMPRAND_COMMON'

# VIP 礼包
HASH_VIP_PACKAGE_RECORD      = 'HASH_VIP_PACKAGE_RECORD'
# 礼包
HASH_LOGIN_PACKAGE           = 'HASH_LOGIN_PACKAGE'
HASH_LEVEL_PACKAGE           = 'HASH_LEVEL_PACKAGE'
HASH_OPENSERVICE_PACKAGE     = 'HASH_OPENSERVICE_PACKAGE'
HASH_ONLINE_PACKAGE          = 'HASH_ONLINE_PACKAGE'
# 豪华签到礼包
HASH_DAILY_PAY_RECORD        = 'HASH_DAILY_PAY_RECORD'
HASH_PAY_LOGIN_PACKAGE       = 'HASH_PAY_LOGIN_PACKAGE'

# 开宝箱
HASH_RANDOM_CHEST            = 'HASH_RANDOM_CHEST_%s'
# 夺宝
HASH_AVOID_WAR_TIME           = 'HASH_AVOID_WAR_TIME'  #玩家免战停止的时间点
TPL_TREASURE_SHARD_GOT        = 'TPL_TREASURE_SHARD_GOT_%s' #获得该碎片的玩家列表信息
HASH_TREASURESHARD_ROBOT_RATE = 'HASH_TREASURESHARD_ROBOT_RATE_%s' #玩家错失该碎片的累计概率
# 精彩活动之 吃桃
HASH_EAT_PEACH                = 'HASH_EAT_PEACH'
HASH_EAT_PEACH_REWARD         = 'HASH_EAT_PEACH_REWARD'
# 精彩活动之 月卡、双月卡
#HASH_MONTHLY_CARD_REWARD      = 'HASH_MONTHLY_CARD_REWARD'
HASH_MONTHLY_CARD             = 'HASH_MONTHLY_CARD'
HASH_DUAL_MONTHLY_CARD        = 'HASH_DUAL_MONTHLY_CARD'

# 精彩活动之成长计划
HASH_GROWTH_PLAN_REWAED       = 'HASH_GROWTH_PLAN_REWAED'
HASH_BUY_GROW_PLAN_TOTAL_NUM      = 'HASH_BUY_GROW_PLAN_TOTAL_NUM'
# 精彩活动之VIP福利
HASH_VIP_WELFARE_REWARD       = 'HASH_VIP_WELFARE_REWARD'     
HASH_VIP_WELFARE_TIME       = 'HASH_VIP_WELFARE_TIME'
# 限时兑换
HASH_EXCHANGE_LIMITED = 'HASH_EXCHANGE_LIMITED' #限时兑换玩家数据
HASH_EXCHANGE_REFRESH_RATE = 'HASH_EXCHANGE_REFRESH_RATE' #限时兑换物品刷新次数，用于计算权重

# 限时神将
HASH_LIMIT_FELLOW_SHRINE     = 'HASH_LIMIT_FELLOW_SHRINE'     # 卡池信息
SET_LIMIT_FELLOW_NAME_SCORE  = 'SET_LIMIT_FELLOW_NAME_SCORE'  # 积分排行榜

# 累计充值
HASH_PAY_ACTIVITY = 'HASH_PAY_ACTIVITY'    # 累计充值

# 累计消费
HASH_CONSUME_ACTIVITY = 'HASH_CONSUME_ACTIVITY'

# 充值返还钻石
HASH_PAY_CREDITS_BACK = 'HASH_PAY_CREDITS_BACK'

# 幸运转盘
HASH_LUCKY_TURNTABLE  = 'HASH_LUCKY_TURNTABLE'


# 邮件
HASH_MAIL_CONTENT             = 'HASH_MAIL_CONTENT_%s_%s'
MAIL_PRIMARY_INC              = 'MAIL_PRIMARY_INC'

# 好友
HASH_FRIENDS_SEND_DOUZHAN     = 'HASH_FRIENDS_SEND_DOUZHAN'
HASH_FRIENDS_GIFT_DOUZHAN     = 'HASH_FRIENDS_GIFT_DOUZHAN_%s'
FRIENDS_DOUZHAN_GET           = 'FRIENDS_DOUZHAN_GET'

# 仙盟
PK_ALLIANCE_ID_AI         = 'PK_ALLIANCE_ID_AI'        #仙盟自增长ID
HASH_ALLIANCE_INFO        = 'HASH_ALLIANCE_INFO'       #仙盟信息
HASH_ALLIANCE_MEMBER      = 'HASH_ALLIANCE_MEMBER'     #仙盟成员信息
TPL_LIST_ALLIANCE_REQUEST = 'LIST_ALLIANCE_REQUEST_%d' #仙盟加入申请
HASH_ALLIANCE_LEVEL       = 'HASH_ALLIANCE_LEVEL'      #仙盟建筑等级信息
HASH_ALLIANCE_HALL        = 'HASH_ALLIANCE_HALL'       #仙盟大殿信息
HASH_ALLIANCE_SACRIFICE   = 'HASH_ALLIANCE_SACRIFICE'  #仙盟女蜗宫信息
HASH_ALLIANCE_LIMIT_ITEM  = 'HASH_ALLIANCE_LIMIT_ITEM' #仙盟商店-珍宝
HASH_ALLIANCE_ITEM        = 'HASH_ALLIANCE_ITEM'       #仙盟商店-道具
HASH_ALLIANCE_LIMIT_ITEM_RANDOM = 'HASH_ALLIANCE_LIMIT_ITEM_RANDOM' #仙盟商店-珍宝的随机次数等信息
HASH_ALLIANCE_MESSAGES    = 'HASH_ALLIANCE_MESSAGES'   #仙盟留言板


# 图鉴
HASH_ATLASLIST_AWARD = 'HASH_ATLASLIST_AWARD'

# 封号、禁言
TYPE_FORBIDDEN = 1 # 玩家封号
TYPE_MUTE      = 2 # 玩家禁言
HASH_SERVER_FORBIDDEN = 'HASH_SERVER_FORBIDDEN'
HASH_SERVER_MUTE      = 'HASH_SERVER_MUTE'

# GM 道具发放
HASH_GM_GRANT_ITEMS   = 'HASH_GM_GRANT_ITEMS'    # GM发放的道具记录
SET_GOT_GRANT_KEYS    = 'SET_GOT_GRANT_KEYS_%s' # 玩家的领取记录

# 每日任务
HASH_DAILY_QUEST = 'HASH_DAILY_QUEST' # 玩家的每日任务的详细信息


# 大乱斗
HASH_JOUST_INFO             = 'HASH_JOUST_INFO'           # 大乱斗基本信息
SET_JOUST_CID_SCORE         = 'SET_JOUST_CID_SCORE'       # 大乱斗的积分排名积分
SET_JOUST_LAST_CID_SCORE    = 'SET_JOUST_LAST_CID_SCORE'  # 大乱斗中上一次的排名积分
HASH_JOUST_ENEMY_INFO       = 'HASH_JOUST_ENEMY_INFO'     # 大乱斗的仇敌列表
HASH_JOUST_HONOR_EXCHANGE   = 'HASH_JOUST_HONOR_EXCHANGE' # 大乱斗中的荣誉兑换

# 玉魄背包
HASH_RANDOM_JADE_LEVEL      = 'HASH_RANDOM_JADE_LEVEL'    # 鉴玉当前等级

# OSS 走马灯配置
HASH_OSS_MESSAGES           = 'HASH_OSS_MESSAGES'
FIELD_BROADCAST             = 'FIELD_BROADCAST'        # 轮播的走马灯内容
FIELD_LIMIT_SHOP_DESC       = 'FIELD_LIMIT_SHOP_DESC'  # 限时商店说明

# 下载资源包领奖记录
HASH_RESOURCE_REWARD        = 'HASH_RESOURCE_REWARD'

#开服七天活动
HASH_OPEN_SERVER_INFO       = 'HASH_OPEN_SERVER_INFO'

# 解救二郎神君
HASH_RESCUE_ER_LANG_GOD     = 'HASH_RESCUE_ER_LANG_GOD'


# 走马灯的消息类型
RORATE_MESSAGE_GM       = 1 # 1: GM消息，优先级最高;
RORATE_MESSAGE_ACTIVITY = 2 # 2：活动消息，优先级次之;
RORATE_MESSAGE_ACHIEVE  = 3 # 3: 玩家成就消息，优先级仅高于本地tips

# 走马灯的成就消息内容
ACHIEVE_TYPE_ADVANCED  = 1 # 神将进阶到+5以上
ACHIEVE_TYPE_RANDCARD  = 2 # 情缘抽到紫将, 包括十连抽
ACHIEVE_TYPE_ARENA     = 3 # 竞技场前十名次发生变动
ACHIEVE_TYPE_RARE_ITEM = 4 # 开箱子开到稀有道具
ACHIEVE_TYPE_LOTTERY   = 5 # 翻牌翻到稀有道具
ACHIEVE_TYPE_LIMIT_FELLOW = 6 # 限时神将抽到紫将
ACHIEVE_TYPE_OPEN_NEWYEAR_PACKAGE = 7 # 新年红包开到宝啦
ACHIEVE_TYPE_LOVER_KISS = 8 #情人之吻
ACHIEVE_TYPE_DIG_TREASURE = 9 #皇陵探宝

RANDCARD_TYPE_GREEN  = 1 # '凡缘'
RANDCARD_TYPE_BLUE   = 2 # '良缘'
RANDCARD_TYPE_PURPLE = 3 # '奇缘'
RANDCARD_TYPE_TEN    = 4 # '奇缘十连抽'
RANDCARD_TYPE_CAMP   = 5 # '阵营抽卡'

RANDCARD_TEN_RATIO   = 97 # 紫卡十连抽打折

# 阵营抽卡
CAMP_RAND_MAX  = 15 # 每个阵营每日最多抽卡次数
CAMP_GROUP_IDS = [[1, 2], [3, 4], [5 ,6]] # 1魏，2蜀，3吴，4群，5妖，6仙
CAMP_RAND_TIME = 172800   # 48h 循环抽卡阵营

#MESSAGE_OF_ACHIEVE = {
#        ACHIEVE_TYPE_ADVANCED: '{0}居然将伙伴{1}进阶到了+{2}.',
#        ACHIEVE_TYPE_RANDCARD: '恭喜{0}在情缘中使用{1}抽卡时抽到了{2}, 吞天噬地指日可待.',
#           ACHIEVE_TYPE_ARENA: '{0}勇猛异常, 夺得了竞技场第{1}名次.',
#       ACHIEVE_TYPE_RARE_ITEM: '天降奇宝, {0}在打开{1}时获得了{2}*{3}.',
#         ACHIEVE_TYPE_LOTTERY: '{0}真是个小红手, 翻牌时居然翻到了{1}*{2}.',
#        }

MAX_CLIENTS_BORADCAST_PER_LOOP = 100

AVOID_WAR_LEVEL       = 12 #  等级<=12级时，玩家也不会出现在夺宝列表中
AVOID_WAR_SECONDS     = 4 * 3600 #每次免战增加时间
AVOID_WAR_CREDITS     = 20 #每次购买免战所需点卷
MAX_USERS_FOR_AVOID   = 10 #每次客户端请求抢夺列表，给的玩家和机器人列表个数上限
MAX_MEMBER_FOR_AVOID  = 20 #玩家打开列表的时候，服务器一共传20个角色数据过来
AVOID_USER_TIME_SPLIT = 10 #能否获取到真实玩家数据的每日时间点
AVOID_USER_TIME_PLUNDER = 180 # 被抢夺玩家CD 3min
ARENA_RANK_REWARD_HOUR  = 22  # 竞技场排行榜奖励时间点, 每日22点

# 不同类型活动的阵容
CAMP_TYPE_ARENA      = 1 # 竞技场排行榜中的玩家阵容
CAMP_TYPE_TREASURE   = 2 # 夺宝中可被抢夺的玩家阵容

# 领奖中心的过期时间
AWARD_VALID_HOURS    = 72 # 14*24 改为3*24
# 领奖中心的奖励类型
AWARD_TYPE_UNKNOWN        = 0 # 未知类型
AWARD_TYPE_FIRSTPAY       = 1 # 首充奖励
AWARD_TYPE_ARENARANK      = 2 # 竞技场排名奖励
AWARD_TYPE_CLIMBING       = 3 # 天外天扫荡奖励
AWARD_TYPE_MONTGLY_CARD   = 4 # 当天未领的月卡奖励
AWARD_TYPE_VIP_WELFARE    = 5 # 当天未领的VIP福利
AWARD_TYPE_LIMIT_FELLOW_RANK  = 6  # 限时神将排名奖励
AWARD_TYPE_LIMIT_FELLOW_SCORE = 7  # 限时神将积分奖励
AWARD_TYPE_PAY_ACTIVITY       = 8  # 累计充值未领的奖励
AWARD_TYPE_CONSUME_ACTIVITY   = 9  # 累计消费未领的奖励
AWARD_TYPE_GIFT_CODE          = 10 # 兑换码礼包奖励
AWARD_TYPE_CONSTELLATION      = 11 # 观星未领的奖励
AWARD_TYPE_SCENE_SWEEP        = 12 # 副本全扫荡掉落
AWARD_TYPE_GM                 = 13 # GM奖励
AWARD_TYPE_ARENA_LUCKY        = 14 # 竞技场幸运排名奖励
AWARD_TYPE_DAILY_QUEST        = 15 # 每日任务未领的奖励
AWARD_TYPE_WORLDBOSS_RANK     = 16 # 世界Boss排名奖励
AWARD_TYPE_PAY_LOGIN          = 17 # 豪华签到未领的奖励
AWARD_TYPE_WORLDBOSS_LASTKILL = 18 # 世界Boss击杀奖励
AWARD_TYPE_JOUSTRANK          = 19 # 大乱斗排名奖励
AWARD_TYPE_PAY_CREDITS_BACK   = 20 # 充值返利
AWARD_TYPE_GROUP_BUY          = 21 # 团购奖励
AWARD_TYPE_RESOURCE_REWARD    = 22 # 第一次下载资源包的奖励

# 玩家的邮件最多保存14天
MAIL_VALID_SECONDS   = 1209600 # 14*24*3600
# 邮件的分页类型
MAIL_PAGE_ALL    = 1 # 全部
MAIL_PAGE_FRIEND = 2 # 好友
MAIL_PAGE_SYSTEM = 3 # 系统
MAIL_PAGE_BATTLE = 4 # 战斗
# 邮件module id
MAIL_BATTLE_1    = 2001  # 决斗场防守成功
MAIL_BATTLE_2    = 2002  # 决斗场被击败
MAIL_BATTLE_3    = 2003  # 决斗场被击败
MAIL_BATTLE_4    = 2101  # 武林大会防守成功
MAIL_BATTLE_5    = 2102  # 武林大会被击败
MAIL_BATTLE_6    = 2201  # 藏宝阁防守成功
MAIL_BATTLE_7    = 2202  # 藏宝阁被抢夺

MAIL_FRIEND_1    = 2301  # 好友申请
MAIL_FRIEND_2    = 2302  # 同意好友申请
MAIL_FRIEND_3    = 2303  # 拒绝好友申请
MAIL_FRIEND_4    = 2304  # 好友留言
MAIL_FRIEND_5    = 2305  # 好友删除 通知自己
MAIL_FRIEND_6    = 2306  # 好友删除 通知对方

MAIL_SYSTEM_1    = 2401  # 决斗场排名奖励
MAIL_SYSTEM_2    = 2402  # 武林大会排名奖励
MAIL_SYSTEM_3    = 2501  # 仙盟 同意申请
MAIL_SYSTEM_4    = 2502  # 仙盟 拒绝申请
MAIL_SYSTEM_5    = 2503  # 仙盟 主动退出仙盟
MAIL_SYSTEM_6    = 2504  # 仙盟 被踢出仙盟


# 好友
FRIEND_RAND_MAX_COUNT   = 20  # 每次随机推荐的玩家数
GET_DOUZHAN_DAILY_LIMIT = 20  # 每日可领取的斗战点最大数
MAX_FRIENDS_COUNT       = 100 # 玩家的最大好友数

# 推送状态有更新的事件ID
SYNC_MULTICATE_TYPE_1 = 1 # 1:领奖中心
SYNC_MULTICATE_TYPE_2 = 2 # 2:精彩活动
SYNC_MULTICATE_TYPE_3 = 3 # 3:聊天
SYNC_MULTICATE_TYPE_4 = 4 # 4:玩家的仙盟权限变更
SYNC_MULTICATE_TYPE_5 = 5 # 5:玩家被踢出仙盟
SYNC_MULTICATE_TYPE_6 = 6 # 6:仙盟的公共信息有变更
SYNC_MULTICATE_TYPE_7 = 7 # 7:玩家被踢出仙盟
SYNC_MULTICATE_TYPE_8 = 8 # 8:精彩活动公告有变更
SYNC_MULTICATE_TYPE_9 = 9 # 9:累计充值活动奖励有变更
SYNC_MULTICATE_TYPE_10 = 10 # 10:累计消费活动奖励有变更


#观星
DICT_CONSTELLATION         = 'DICT_CONSTELLATION' #本日观星数据
CONSTELLATION_FREE_REFRESH = 2                    #当日观星可免费次数
CONSTELLATION_SELECT_MAX         = 20             #觀星當日次數上限
CONSTELLATION_CREDITS_FOR_FREE   = 10             #刷新观星所需钻石
CONSTELLATION_CREDITS_FOR_REWARD = 30             #刷新观星奖励所需钻石

# 副本全扫荡 需10个钻石
SCENE_ALL_SWEEP_COST = 20
# 重置怪物组挑战次数的方式
SCENE_RESET_ITEM   = 1 # 使用道具
SCENE_RESET_CREDIT = 2 # 使用钻石

# 扫荡副本的方式
SCENE_SWEEP_ITEM   = 1 # 使用道具
SCENE_SWEEP_CREDIT = 2 # 使用钻石

# 购买冷却时间, 60s = 1 credits
COOLDOWN_TIME_COST = 60
# 天外天 购买1次挑战次数，需要10个钻石
CLIMBING_FIGHT_COST = 10
# 精英副本默认挑战次数
ELITESCENE_FIGHT_COUNT = 3
REVIVE_BASIC_GOLDS     = 200 # 复活初始价格为200金币
# 活动副本ID
ACTIVE_PANDA_ID        = 301001 # 活动副本之经验熊猫ID
ACTIVE_TREASURE_ID     = 301002 # 活动副本之经验宝物ID
ACTIVE_TREE_ID         = 301003 # 活动副本之打土豪ID

# 战斗类型
FIGHT_TYPE_NORMAL     = 1 # 剧情副本
FIGHT_TYPE_ELITE      = 2 # 精英副本
FIGHT_TYPE_PANDA      = 3 # 活动副本之经验熊猫
FIGHT_TYPE_TREASURE   = 4 # 活动副本之经验宝物
FIGHT_TYPE_TREE       = 5 # 活动副本之打土豪
FIGHT_TYPE_CLIMBING   = 6 # 天外天

# 精彩活动ID
EXCITE_FIRSTPAY         = 1  # 首充奖励
EXCITE_EAT_PEACH        = 2  # 吃桃
EXCITE_GROWTH_PLAN      = 3  # 成长计划
EXCITE_ACTIVITY_NOTICE  = 4  # 活动公告
EXCITE_MYSTICALSHOP     = 5  # 神秘商店
EXCITE_VIP_WELFARE      = 6  # VIP福利
EXCITE_LIMIT_FELLOW     = 7  # 限时神将
EXCITE_EXCHANGE_LIMITED = 8  # 限时兑换
EXCITE_MONTHLY_CARD     = 10 # 月卡
EXCITE_PAY_ACTIVITY     = 11 # 累计充值
EXCITE_CONSUME_ACTIVITY = 12 # 累计消费
EXCITE_NEWYEAR_PACKAGE  = 13 # 新年红包
EXCITE_HAPPY_NEW_YEAR   = 14 # 恭贺新禧
EXCITE_PAY_CREDITS_BACK = 15 # 充值返钻石
EXCITE_LOVER_KISS       = 16 # 情人之吻
EXCITE_DIG_TREASURE     = 17 # 皇陵探宝
EXCITE_LUCKY_TURNTABLE  = 18 # 幸运转盘
EXCITE_GROUP_BUY        = 19 # 限时团购
EXCITE_TIME_LIMIT_SHOP  = 20 # 限时商店

CHAT_MSG_QUEUE_MAX_LEN     = 200 # 消息队列最多保存200条消息
CHAT_MSG_LOGOUT_MAX_LEN    = 50  # 登陆加载最近50条聊天消息
CHAR_MSG_BROADCAST_MAX_LEN = 50  # 单次广播的消息数
CHAT_BROADCAST_INTERVAL    = 5   # 群聊广播的时间间隔

# 同步玩家的数据的类型
SYNC_NICK_NAME  = 1  # 同步玩家昵称
SYNC_LEAD_ID    = 2  # 同步玩家的角色ID
SYNC_VIP_LEVEL  = 3  # 同步玩家的VIP等级
SYNC_LEVEL      = 4  # 同步玩家的等级
SYNC_MIGHT      = 5  # 同步玩家的战力
SYNC_ARENA_RANK = 6  # 同步玩家的竞技场排名

#仙盟相关
ALLIANCES_PER_PAGE        = 10
ALLIANCE_CREATE_GOLDS     = 500000            
ALLIANCE_CREATE_CREDITS   = 500

ALLIANCE_POSITION_NONE    = 0 # 不在仙盟中
ALLIANCE_POSITION_LEADER  = 1 # 会长
ALLIANCE_POSITION_VICE    = 2 # 副会长
ALLIANCE_POSITION_NORMAL  = 3 # 会员

ALLIANCE_REQUEST_MAX = 3 # 最多对3个仙盟提出申请
ALLIANCE_VICE_MAX    = 3 # 一个仙盟最多3个副会长

ALLIANCE_REQUEST_REJECT = 1 # 拒绝
ALLIANCE_REQUEST_AGREE  = 2 # 同意

ALLIANCE_LEAVE_CD_TIME  = 86400 # 24*60*60

ALLIANCE_SACRIFICE_NORMAL   = 1   # 拜祭方式之消耗个人贡献拜祭
ALLIANCE_SACRIFICE_CREDITS  = 2   # 拜祭方式之消耗钻石拜祭
SACRIFICE_NEED_CONTRIBUTION = 50  # 所需个人贡献点数
SACRIFICE_NEED_CREDITS      = 30  # 所需钻石数

ALLIANCE_DESC    = 1 # 仙盟宣言
ALLIANCE_NOTICE  = 2 # 仙盟公告

MESSAGES_VALID_HOUR   = 168 # 每条留言只能保留7天 24*7
MESSAGES_DAILY_MAX    = 3   # 每日最多可留言3次
MESSAGES_COUNT_LIMIT  = 50  # 最多保持50条留言

# 仙盟动态类型
ACTION_PER_PAGE     = 20    # 每次返回20条动态
ACTION_COUNT_LIMIT  = 50    # 最多保存50条动态
ALLIANCE_ACTION_1   = 3001  # 加入仙盟
ALLIANCE_ACTION_2   = 3002  # 退出仙盟
ALLIANCE_ACTION_3   = 3003  # 被踢出仙盟
ALLIANCE_ACTION_4   = 3004  # 转让盟主
ALLIANCE_ACTION_5   = 3005  # 任命为副盟主
ALLIANCE_ACTION_6   = 3006  # 大殿金币建设
ALLIANCE_ACTION_7   = 3007  # 大殿钻石建设
ALLIANCE_ACTION_8   = 3008  # 参拜女蜗宫
ALLIANCE_ACTION_9   = 3009  # 仙盟升级
ALLIANCE_ACTION_10  = 3010  # 盟主罢免副盟主


# 限时神将
LIMIT_FELLOW_FREE_TIME  = 72000 # 免费抽卡的循环时间
LIMIT_FELLOW_RAND_COST  = 268   #  钻石抽卡消耗
RANDCARD_TYPE_FREE      = 1     # 免费抽卡
RANDCARD_TYPE_CREDITS   = 2     # 钻石抽卡
# 每获得150积分可以额外获得一次额外的免费钻石抽卡机会
RAND_COST_FREE_SCORE    = 150   
RANDCARD_ONCE_SCORE     = 10    # 一次抽卡获得10积分


# 图鉴
CATEGORY_TYPE_FELLOW    = 1  # 伙伴
CATEGORY_TYPE_EQUIP     = 2  # 装备
CATEGORY_TYPE_TREASURE  = 3  # 宝物

# 好感度
EXCHANGE_GOODWILL_COST  = 50 # 每次交换费用均是钻石50

#世界Boss
DICT_WORLDBOSS_INFO = 'DICT_WORLDBOSS_INFO'
RANK_WORLDBOSS_DAMAGE = 'RANK_WORLDBOSS_DAMAGE'
DICT_WORLDBOSS_ATTACKER_DATA = 'DICT_WORLDBOSS_ATTACKER_DATA'
DICT_WORLDBOSS_RANKER_DATA = 'DICT_WORLDBOSS_RANKER_DATA'

# 每日任务相关
DAILY_QUEST_ID_1   = 1   # 刷新神秘商店
DAILY_QUEST_ID_2   = 2   # 完成精英副本
DAILY_QUEST_ID_3   = 3   # 完成剧情副本
DAILY_QUEST_ID_4   = 4   # 完成活动副本
DAILY_QUEST_ID_5   = 5   # 参与夺宝
DAILY_QUEST_ID_6   = 6   # 参与决斗场
DAILY_QUEST_ID_7   = 7   # 进行观星
DAILY_QUEST_ID_8   = 8   # 进行洗练
DAILY_QUEST_ID_9   = 9   # 攻打天外天
DAILY_QUEST_ID_10  = 10  # 赠送好友斗战点
DAILY_QUEST_ID_11  = 11  # 签到
DAILY_QUEST_ID_12  = 12  # 吃桃
DAILY_QUEST_ID_13  = 13  # 神将
DAILY_QUEST_ID_14  = 14  # 装备强化
DAILY_QUEST_ID_15  = 15  # 宝物强化
DAILY_QUEST_ID_16  = 16  # 前往商城招募伙伴
DAILY_QUEST_ID_17  = 17  # 购买精力丸
DAILY_QUEST_ID_18  = 18  # 购买兵粮丸

DAILY_QUEST_DONE   = 1   # 每日任务中的子任务状态, 0-未完成, 1-已完成


# 大乱斗
JOUST_FREE_COUNT      = 20     # 玩家初始有20次挑战次数
JOUST_BASIC_SCORE     = 1000   # 活动初始, 参与活动的玩家拥有1000积分
JOUST_ROBOT_CID       = 10000  # <10000时为机器人

JOUST_HONOR = 2 # 战斗胜利后的荣誉奖励

SATURDAY = 6 # 星期6
SUNDAY   = 7 # 星期7

JOUST_HOUR_START = 8  # 一天中活动开始的hour 8点
JOUST_HOUR_END   = 23 # 一天中活动结束的hour 23点

RANK_RANGE = 100 # 随机的玩家排名范围为前后100名

SCORE_RATE_2  = 2     # 积分的2%
SCORE_RATE_3  = 3     # 积分的3%
SCORE_RATE_4  = 4     # 积分的4%
SCORE_PERCENT = 100   # 积分的百分比

SCORE_BASIC_2    = 20 # 基础积分20分
SCORE_BASIC_3    = 30 # 基础积分30分
SCORE_BASIC_4    = 40 # 基础积分40分

JOUST_ENEMY_LIMIT = 20 # 最多保存最近的20名玩家

JOUST_BATTLE_NORMAL   = 1 # 普通挑战
JOUST_BATTLE_REVERGE  = 2 # 复仇

#新年红包
DICT_NEWYEAR_PACKAGE = 'DICT_NEWYEAR_PACKAGE'
LIST_NEWYEAR_RECEIVED_CHAR = 'LIST_NEWYEAR_RECEIVED_CHAR'

#随机礼包计数器
HASH_PACKAGE_SERVER_COUNTER   = 'HASH_PACKAGE_SERVER_COUNTER'
HASH_PACKAGE_PERSONAL_COUNTER = 'HASH_PACKAGE_PERSONAL_COUNTER_%s'
#情人之吻
BLUE_ROSE_MAX_NUM                 = 60      # BLUE ROSE最大数量
NORMAL_ROSE_MAX_NUM               = 5       # 普通玫瑰
DICT_LOVER_KISS                   = 'DICT_LOVER_KISS'

# 充值返利
PAY_CREDITS_BACK_MAX = 20000 # 活动期间最多返利有上限2万

# 限时商店
LIST_TIME_LIMITED_GROUP      = 'LIST_TIME_LIMITED_GROUP'      #商品组时间段配置
LIST_TIME_LIMITED_SHOP       = 'LIST_TIME_LIMITED_SHOP'       #商品列表
DICT_TIME_LIMITED_SHOP_BUYED = 'DICT_TIME_LIMITED_SHOP_BUYED' #已购买玩家记录。key:cid, value:marshal格式，反序列化之后：((id, buyed_count, last_buy_t), ...)

#一键转化的价格
BATCH_DECOMPOSE_PRICE = 10 #每N个绿伙伴1个钻石

#恭贺新禧
GONG = 90018
HE = 90019
XIN = 90020
XI = 90021
HAPPY_NEW_YEAR = [GONG, HE, XIN, XI]
HAPPY_NEW_YEAR_PACKAGE = 90022

#皇陵探宝
DICT_DIG_TREASURE_INFO = "DICT_DIG_TREASURE_INFO"
FREE_DIG = 0
CREDITS_DIG = 1


# 玉魄
JADE_PER_PAGE              = 50 # 玉魄每次请求每页50条
JADE_RANDOM_TIMES_TEN      = 10 # 连续10次单次鉴玉
JADE_RANDOM_POOLS          = [0, 90009, 90010, 90011, 90012, 90013] # 鉴玉奖池, 下标对应鉴玉等级
JADE_UPGRADE_CHEST_ID      = 90014 # 召唤宝玉的奖池

# 角色等级达到50级以上或VIP等级5以上才可进行快速鉴玉
JADE_RANDOM_TEN_LEVEL      = 50 
JADE_RANDOM_TEN_VIP_LEVEL  = 5

JADE_UPGRADE_LEVEL_CREDITS = 50 # 提升当前鉴玉等级所需钻石
JADE_UPGRADE_LEVEL         = 4  # 直接将当前鉴玉等级提升到的等级

# 依次为白品,绿品,蓝品,紫品,橙品, 下标依次为0,1,2,3,4
JADE_STRENGTHEN_EXP = ['WhiteExp', 'GreenExp', 'BlueExp', 'PurpleExp', 'OrangeExp']

# 幸运转盘
TURNTABLE_ITEM_POOLS = [0, 90015, 90016, 90017] # 转盘道具池 下标对应转盘档位

#限时团购
DICT_GROUP_BUY_INFO = "DICT_GROUP_BUY_INFO"
DICT_GROUP_BUY_PERSON_INFO = "DICT_GROUP_BUY_PERSON_INFO"

# 功能开放 
FUNCTION_SCENE_SWEEP      = 63  # 全部扫荡
FUNCTION_DAILY_QUEST      = 64  # 每日任务
FUNCTION_TEN_PLUNDER      = 75  # 宝物十连抢
FUNCTION_OPEN_SERVER_ACTIVITY = 76 #开服七天活动
FUNCTION_ACHIEVEMENT      = 77  #成就

# 双月卡
MONTHLY_CARD_NORMAL       = 2 # 月卡类型-普通月卡
MONTHLY_CARD_DUAL         = 3 # 月卡类型-双月卡

MONTHLY_CARD_TODAY        = 1 # 月卡奖励-今日奖励
MONTHLY_CARD_PREV         = 2 # 月卡奖励-昨日奖励




# 游戏限制
LIMIT_ID_SCENE_SWEEP       = 4  # 副本全部扫荡花费
LIMIT_ID_JADE_COST         = 11 # 鉴玉提升到宝玉价格
LIMIT_ID_MONTHLY_CARD      = 12 # 25元月卡补领价格
LIMIT_ID_DUAL_MONTHLY_CARD = 13 # 50元月卡补领价格
LIMIT_ID_ER_LANG_VIP_LEVEL = 14 # 解救天神-可立即领取VIP限制
LIMIT_ID_ER_LANG_GOD_ID    = 15 # 天神的ID


#开服狂欢任务id
OPEN_SERVER_QUEST_ID_1 = 1 #登陆奖励
OPEN_SERVER_QUEST_ID_2 = 2 #充值奖励
OPEN_SERVER_QUEST_ID_3 = 3 #副本
OPEN_SERVER_QUEST_ID_4 = 4 #等级
OPEN_SERVER_QUEST_ID_5 = 5 #装备品质
OPEN_SERVER_QUEST_ID_6 = 6 #装备强化
OPEN_SERVER_QUEST_ID_7 = 7 #决斗场
OPEN_SERVER_QUEST_ID_8 = 8 #夺宝
OPEN_SERVER_QUEST_ID_9 = 9 #合成蓝色宝物
OPEN_SERVER_QUEST_ID_10 = 10 #天外天
OPEN_SERVER_QUEST_ID_11 = 11 #混沌
OPEN_SERVER_QUEST_ID_12 = 12 #精英
OPEN_SERVER_QUEST_ID_13 = 13 #神秘商店
OPEN_SERVER_QUEST_ID_14 = 14 #战斗力
OPEN_SERVER_QUEST_ID_15 = 15 #鉴玉
OPEN_SERVER_QUEST_ID_16 = 16 #蓝品玉魄
OPEN_SERVER_SHOP = 17 #shop #商店
OPEN_SERVER_QUEST_LIST = [OPEN_SERVER_QUEST_ID_1,OPEN_SERVER_QUEST_ID_2,OPEN_SERVER_QUEST_ID_3, OPEN_SERVER_QUEST_ID_4, OPEN_SERVER_QUEST_ID_5, OPEN_SERVER_QUEST_ID_6, OPEN_SERVER_QUEST_ID_7, OPEN_SERVER_QUEST_ID_8, OPEN_SERVER_QUEST_ID_9, OPEN_SERVER_QUEST_ID_10, OPEN_SERVER_QUEST_ID_11, OPEN_SERVER_QUEST_ID_12 ,OPEN_SERVER_QUEST_ID_13, OPEN_SERVER_QUEST_ID_14,OPEN_SERVER_QUEST_ID_15, OPEN_SERVER_QUEST_ID_16]

#成就
ACHIEVEMENT_QUEST_ID_3 = 3 #副本
ACHIEVEMENT_QUEST_ID_4 = 4 #等级
ACHIEVEMENT_QUEST_ID_5 = 5 #装备品质
ACHIEVEMENT_QUEST_ID_6 = 6 #装备强化
ACHIEVEMENT_QUEST_ID_7 = 7 #决斗场
ACHIEVEMENT_QUEST_ID_8 = 8 #夺宝
ACHIEVEMENT_QUEST_ID_9 = 9 #合成蓝色宝物
ACHIEVEMENT_QUEST_ID_10 = 10 #天外天
ACHIEVEMENT_QUEST_ID_11 = 11 #混沌
ACHIEVEMENT_QUEST_ID_12 = 12 #精英
ACHIEVEMENT_QUEST_ID_13 = 13 #神秘商店
ACHIEVEMENT_QUEST_ID_14 = 14 #战斗力
ACHIEVEMENT_QUEST_ID_15 = 15 #鉴玉
ACHIEVEMENT_QUEST_ID_16 = 16 #蓝品玉魄

ACHIEVEMENT_QUEST_ID_18 = 18 #vip等级
ACHIEVEMENT_QUEST_ID_19 = 19 #大乱斗
ACHIEVEMENT_QUEST_ID_20 = 20 #好友数量
ACHIEVEMENT_QUEST_ID_21 = 21 #参加魔主次数
ACHIEVEMENT_QUEST_ID_22 = 22 #上阵伙伴数量
ACHIEVEMENT_QUEST_ID_23 = 23 #神将好感总等级
ACHIEVEMENT_QUEST_ID_24 = 24 #仙盟等级
ACHIEVEMENT_QUEST_ID_25 = 25 #玉魄种类数量
ACHIEVEMENT_QUEST_ID_26 = 26 #装备种类数量
ACHIEVEMENT_QUEST_ID_27 = 27 #宝物种类
ACHIEVEMENT_QUEST_ID_28 = 28 #伙伴最高等级
ACHIEVEMENT_QUEST_ID_29 = 29 #蓝色伙伴数量
ACHIEVEMENT_QUEST_ID_30 = 30 #紫色
ACHIEVEMENT_QUEST_ID_31 = 31 #橙色
ACHIEVEMENT_QUEST_ID_32 = 32 #装备洗练次数
ACHIEVEMENT_QUEST_ID_33 = 33 #宝物精炼等级
ACHIEVEMENT_QUEST_ID_34 = 34 #上阵伙伴全部装备精炼等级

HASH_ACHIEVEMENT_INFO = 'HASH_ACHIEVEMENT_INFO'

#新走马灯
HASH_NEW_BROAD_MESSAGE = 'hash_new_broad_message'

# -------------------------log constant------------------------------
LOG_CHAR_NEW     = 1001 # 用户新建
LOG_CHAR_NEW_1   = 10011 # 用户新建 新增login_type信息
LOG_LOGIN        = 1002 # 用户登录   
LOG_LOGOUT       = 1003 # 用户登出
LOG_LEVELUP      = 1010 # 用户升级
LOG_TUTORIAL     = 1011 # 用户教程
LOG_PAYMENT      = 1020 # 用户充值

LOG_GOLD_GET             = 2001     # 金币的获得
LOG_GOLD_LOSE            = 2002     # 金币的失去
LOG_CREDITS_GET          = 2003     # 钻石的获得
LOG_CREDITS_LOSE         = 2004     # 钻石的失去
LOG_ITEM_GET             = 2005     # 道具的获得
LOG_ITEM_LOSE            = 2006     # 道具的失去
LOG_PRESTIGE_GET         = 2007     # 声望的获得
LOG_PRESTIGE_LOSE        = 2008     # 声望的失去
LOG_SCENESTAR_GET        = 2009     # 副本星星的获得
LOG_SCENESTAR_LOSE       = 2010     # 副本星星的失去
LOG_FELLOW_GET           = 2011     # 伙伴的获得
LOG_FELLOW_STRENGTHEN    = 2012     # 伙伴的强化
LOG_FELLOW_REFINE        = 2013     # 伙伴的突破
LOG_CHAR_EXP_GET         = 2014     # 主角经验获得
LOG_EQUIP_STRENGTHEN     = 2015     # 装备的强化
LOG_EQUIP_REFINE         = 2016     # 装备的洗炼
LOG_TREASURE_STRENGTHEN  = 2017     # 宝物的强化
LOG_TREASURE_REFINE      = 2018     # 宝物的精炼
LOG_MYSTERY_GET          = 2019     # 神秘商店
LOG_SCENE_BATTLE         = 2020     # 副本战斗
LOG_FELLOW_DECOMPOSITION = 2021     # 伙伴炼化
LOG_GIFT_CODE_USE        = 2022     # 兑换码使用记录
LOG_PAY_CREDITS_BACK     = 2023     # 充值返利
LOG_ALLIANCE_CREATE      = 2024     # 仙盟新建
LOG_ALLIANCE_DISSOLVE    = 2025     # 仙盟解散
LOG_ALLIANCE_EXP_GET     = 2026     # 仙盟建设度的获得
LOG_ALLIANCE_EXP_LOSE    = 2027     # 仙盟建设度的失去
LOG_CONTRIBUTE_GET       = 2028     # 仙盟个人贡献度的获得
LOG_CONTRIBUTE_LOSE      = 2029     # 仙盟个人贡献度的失去
LOG_ALLIANCE_POSITION    = 2030     # 仙盟个人职位的变更
LOG_AVOID_WAR            = 2031     # 夺宝
LOG_CLIMB_TOWER          = 2032     # 天外天单层
LOG_OPEN_SERVICE_PACKAGE = 2033     # 开服礼包
LOG_SHOP_BUY             = 2034     # 商店购买

# 途径定义
WAY_UNKNOWN                       = 10000   # 未知途径
WAY_RANDCARD_ITEM                 = 10001   # 商城道具抽卡
WAY_RANDCARD_BLUE                 = 10002   # 商城蓝卡抽卡
WAY_RANDCARD_PURPLE               = 10003   # 商城紫卡抽卡
WAY_RANDCARD_TEN                  = 10004   # 商城紫卡十连抽抽卡
WAY_ITEM_SHOP                     = 10005   # 商城道具商店
WAY_VIP_PACKAGE_SHOP              = 10006   # 商城VIP礼包

WAY_VIP_WELFARE                   = 10007   # VIP福利

WAY_SCENE_CHEST                   = 10008   # 剧情副本星数宝箱奖励
WAY_SCENE_DROP                    = 10009   # 剧情副本掉落
WAY_SCENE_BATTLE                  = 10010   # 剧情副本战斗奖励
WAY_SCENE_CD_TIME                 = 10011   # 剧情副本冷却时间

WAY_ELITESCENE_BATTLE             = 10012   # 精英副本战斗奖励
WAY_ELITESCENE_REVIVE             = 10013   # 精英副本复活
WAY_ELITESCENE_FIGHT              = 10014   # 精英副本挑战

WAY_ACTIVESCENE_TREE_FIGHT        = 10015   # 活动副本之打土豪挑战
WAY_ACTIVESCENE_TREASURE_FIGHT    = 10016   # 活动副本之经验宝物挑战
WAY_ACTIVESCENE_PANDA_FIGHT       = 10017   # 活动副本之经验萌熊挑战

WAY_CONSTELLATION_REFRESH         = 10018   # 观星刷新
WAY_CONSTELLATION_AWARD_REFRESH   = 10019   # 观星奖励内容刷新
WAY_CONSTELLATION_AWARD           = 10020   # 观星奖励

WAY_EQUIP_STRENGTHEN              = 10021   # 装备普通强化
WAY_EQUIP_STRENGTHEN_AUTO         = 10022   # 装备自动强化
WAY_EQUIP_REFINE                  = 10023   # 装备普通洗炼
WAY_EQUIP_REFINE_GOLD             = 10024   # 装备金币洗炼
WAY_EQUIP_REFINE_HIGH             = 10025   # 装备高级洗炼
WAY_EQUIP_REFINE_REPLACE          = 10026   # 装备替换洗炼属性
WAY_EQUIP_REBORN                  = 10027   # 装备重生

WAY_FELLOW_STRENGTHEN             = 10028   # 伙伴强化
WAY_FELLOW_SOUL_STRENGTHEN        = 10029   # 伙伴仙魂强化
WAY_FELLOW_REFINE                 = 10030   # 伙伴突破
WAY_FELLOW_REBORN                 = 10031   # 伙伴重生

WAY_TREASURE_STRENGTHEN           = 10032   # 宝物强化
WAY_TREASURE_REFINE               = 10033   # 宝物精炼
WAY_TREASURE_REBORN               = 10034   # 宝物重生

WAY_BAG_EXPAND                    = 10035   # 背包扩充
WAY_GROWTH_PLAN                   = 10036   # 成长计划
WAY_MYSTICAL_SHOP                 = 10037   # 神秘商店
WAY_FIRSTPAY                      = 10038   # 首充 
WAY_CREDITS_PAYMENT               = 10039   # vip充值
WAY_MONTHLY_CARD                  = 10040   # 月卡充值
WAY_MONTHLY_CARD_AWARD            = 10041   # 月卡奖励
WAY_FIRSTPAY_AWARD                = 10042   # 首充奖励

WAY_LIMIT_EXCHANGE                = 10043   # 限时兑换
WAY_LIMIT_EXCHANGE_REFRESH        = 10044   # 刷新限时兑换
WAY_LIMIT_EXCHANGE_LOCK           = 10045   # 锁定限时兑换
WAY_LIMIT_FELLOW                  = 10046   # 限时神将
WAY_LIMIT_FELLOW_RANDCARD         = 10047   # 限时神将抽卡

WAY_OPENSERVICE_PACKAGE           = 10048   # 开服礼包 
WAY_LEVELUP_PACKAGE               = 10049   # 等级礼包
WAY_LOGIN_PACKAGE                 = 10050   # 签到礼包
WAY_ONLINE_PACKAGE                = 10051   # 在线礼包

WAY_CLIMBING_RESET                = 10052   # 天外天重置
WAY_CLIMBING_FIGHT                = 10053   # 天外天挑战
WAY_CLIMBING_DONE                 = 10054   # 天外天立即完成
WAY_CLIMBING_AWARD                = 10055   # 天外天奖励

WAY_USE_CHEST                     = 10056   # 开宝箱
WAY_LOTTERY_AWARD                 = 10057   # 翻牌奖励
WAY_GM_AWARD                      = 10058   # 官方GM奖励
WAY_ATLASLIST_AWARD               = 10059   # 图鉴奖励
WAY_AVOID_WAR                     = 10060   # 夺宝免战

WAY_ARENA_RANK_AWARD              = 10061   # 竞技场排名奖励
WAY_ARENA_EXCHANGE                = 10062   # 竞技场声望兑换
WAY_ARENA_LUCK_RANK               = 10063   # 竞技场幸运排行

WAY_GOODWILL_EXCHANGE             = 10064   # 神将好感度互换 
WAY_CHAOS_UPDATE                  = 10065   # 混沌升级
WAY_ALLIANCE_CREATE               = 10066   # 创建仙盟

WAY_SHARD_COMBINE                 = 10067   # 碎片合成
WAY_FELLOW_DECOMPOSITION          = 10068   # 伙伴炼化
WAY_EQUIP_DECOMPOSITION           = 10069   # 装备炼化
WAY_TREASURE_DECOMPOSITION        = 10070   # 宝物炼化

WAY_ITEM_USE                      = 10071   # 道具背包使用道具
WAY_ELITESCENE_DROP               = 10072   # 精英副本掉落
WAY_PAY_ACTIVITY                  = 10073   # 累计充值
WAY_CONSUME_ACTIVITY              = 10074   # 累计消费
# 商城道具商店中的商品
WAY_CHEST_GOLD                    = 10075   # 黄金宝箱
WAY_KEY_GOLD                      = 10076   # 黄金钥匙
WAY_CHEST_SILVER                  = 10077   # 白银宝箱
WAY_KEY_SILVER                    = 10078   # 白银钥匙
WAY_CHEST_BRONZE                  = 10079   # 青铜宝箱
WAY_KEY_BRONZE                    = 10080   # 青铜钥匙
WAY_SHOP_GOLD                     = 10081   # 金币相关
WAY_EXP_PANDA                     = 10082   # 经验萌熊
WAY_ENERGY_WAN                    = 10083   # 精力丸相关
WAY_BINGLIANG_WAN                 = 10084   # 兵粮丸相关

WAY_ALLIANCE_HALL_CONTRIBUTE      = 10085   # 仙盟大殿建设
WAY_ALLIANCE_SACRIFICE            = 10086   # 仙盟女蜗宫
WAY_ALLIANCE_LIMIT_ITEM           = 10087   # 仙盟商店-珍宝
WAY_ALLIANCE_ITEM                 = 10088   # 仙盟商店-道具

WAY_ARENA_BATTLE                  = 10089   # 竞技场挑战
WAY_SCENE_ALL_SWEEP               = 10090   # 副本全扫荡
WAY_GIFT_CODE                     = 10091   # 兑换码兑换

WAY_DAILY_QUEST                   = 10092   # 每日任务
WAY_WORLDBOSS_CLEAR_CD            = 10093   #世界BOSS清CD
WAY_WORLDBOSS_BOOST               = 10094   #世界BOSS鼓舞
WAY_WORLDBOSS                     = 10095   #世界BOSS
WAY_WORLDBOSS_RANK                = 10096   #世界BOSS排名奖励
WAY_WORLDBOSS_KILL                = 10097   #世界BOSS击杀奖励

WAY_PAY_LOGIN_PACKAGE             = 10100   # 豪华签到礼包
WAY_PAY_CREDITS_BACK              = 10101   # 充值返利
WAY_LOVER_KISS                    = 10102   # 情人之吻
WAY_HAPPY_NEW_YEAR                = 10103   # 恭贺新禧
WAY_NEW_YEAR_PACKAGE              = 10104   # 新年红包

WAY_JOUST_RANK_AWARD              = 10110   # 大乱斗排名奖励
WAY_JOUST_EXCHANGE                = 10111   # 大乱斗兑换
WAY_JOUST_BATTLE_COUNT            = 10112   # 大乱斗挑战次数

WAY_BATCH_DECOMPOSE               = 10116   # 一键转化
WAY_SELL_EQUIP                    = 10117   # 出售装备
WAY_SELL_TREASURE                 = 10118   # 出售宝物
WAY_SELL_ITEM                     = 10119   # 出售道具

WAY_ALLIANCE_HALL                 = 10121   # 仙盟大殿
WAY_ALLIANCE_SACRIFICE_CREDITS    = 10122   # 仙盟女蜗宫 钻石参拜
WAY_ALLIANCE_SACRIFICE_NORMAL     = 10123   # 仙盟女蜗宫 普通参拜

WAY_ALLIANCE_HALL_CONTRIBUTE_IDS  = [0, 10124, 10125, 10126, 10127]
# 10124 仙盟大殿 初级建设
# 10125 仙盟大殿 中级建设
# 10126 仙盟大殿 高级建设
# 10127 仙盟大殿 顶级建设
WAY_ALLIANCE_SHOP                  = 10128   # 仙盟商店
WAY_ALLIANCE_BUILD = [0, WAY_ALLIANCE_HALL, WAY_ALLIANCE_SACRIFICE, WAY_ALLIANCE_SHOP]
WAY_DIG_TREASURE_FREE              = 10129   # 免费皇陵探宝
WAY_DIG_TREASURE_CREDITS           = 10130   # 钻石探宝
WAY_AVOID_WAR                      = 10131   # 夺宝
WAY_CLIMB_TOWER_SINGLE             = 10132   # 天外天单层
WAY_CLIMB_TOWER_START              = 10133   # 天外天扫荡
WAY_CLIMB_TOWER_FINISH             = 10134   # 天外天立即完成
WAY_DIRECT_PACKAGE                 = 10135   # 定向礼包


WAY_JADE_RANDOM                    = 10141   # 玉魄-鉴玉
WAY_JADE_UPGRADE_LEVEL             = 10142   # 玉魄-召唤宝玉

WAY_LUCKY_TURNTABLE                = 10146   # 幸运转盘

WAY_TIME_LIMITED_SHOP              = 10150   # 限时商店购买
WAY_GROUP_BUY                      = 10151   # 团购
WAY_RESOURCE_REWARD                = 10052   # 下载资源包
WAY_GROWTH_PLAN_WELFARE            = 10054   # 成长计划福利
WAY_EAT_PEACH                      = 10055   # 吃桃

WAY_SCENE_DUNGEON_CHEST            = 10056   # 剧情副本 怪物组宝箱奖励
WAY_SCENE_RESET                    = 10057   # 剧情副本 重置挑战次数

WAY_CAMP_RANDCARD                  = 10059   # 阵营抽卡

WAY_DUAL_MONTHLY_CARD              = 10061   # 双月卡

WAY_OPEN_SERVER_ACTIVITY_BUY       = 10062   # 开服活动商店购买
WAY_OPEN_SERVER_ACTIVITY_GOT       = 10063   # 开服活动领取

WAY_ACHIEVEMENT                    = 10064   # 成就系统

WAY_TO_NAMED                       = 10065   #改名
