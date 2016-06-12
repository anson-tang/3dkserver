#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

'''
used redis record:
    type    : Hash
    key_name:  
    format  :  
    others  :  
    used to :  
    example :  

    type    : Hash
    key_name: HASH_ITEM_SHOP_RECORD 
    format  : key_name cid marshal.dumps(data) 
    others  : data=[last_buyed_time, [[id, num], ...]]
    used to : 道具商店购买记录 
    example :  

    type    : Hash
    key_name: HASH_RESCUE_ER_LANG_GOD
    format  : key_name cid end_timestamp ...
    others  :  
    used to : 解救女神 
    example :  

    type    : Hash
    key_name:  
    format  :  
    others  :  
    used to :  
    example :  

    type    : Hash
    key_name: HASH_FINISHED_DIALOGUE_GROUP 
    format  : key_name cid marshal.dumps(data)
    others  : data = [finished_group_id, ...] 
    used to : 玩家已完成的剧情对话组ID记录
    example :  

    type    : Hash
    key_name: HASH_CHARACTER_CAMP
    format  : key_name cid marshal.dumps(data) cid marshal.dumps(data) ...
    others  : data = get_player_camp
    used to : 竞技场中最多5千个玩家阵营的阵容
    example : 

    type    : Hash
    key_name: HASH_ACTIVITY_LOTTERY
    format  : key_name cid marshal.dumps(data) cid marshal.dumps(data) ...
    others  : data = [(role_lvl, vip_lvl), {id: count, id: count}]
    used to : 活动中的翻牌 随机三个道具 并记录未被抽中的次数 抽中后归零
    example : 

    type    : Hash
    key_name: HASH_ARENA_RANK
    format  : key_name rank marshal.dumps(detail) rank marshal.dumps(detail) ... 
    others  : detail = [cid, lvl, nick_name, rank, award['gold'], award['prestige'], fellow_ids]
    used to : 竞技场中最多5千个排名及其对应的详情
    example :  

    type    : Sorted Set
    key_name: SET_ARENA_CID_RANK
    format  : key_name rank cid rank cid ...
    others  : 竞技场中进入五千个排名的玩家 
    used to :  
    example :  

    type    : Hash
    key_name: HASH_ARENA_LUCKY_RANKLIST 
    format  : key_name LUCKY_RANKLIST marshal.dumps(detail)
    others  : detail = [[[last_rank, nick_name, credits], ...], [[cur_rank, credits], ...]]
    used to : 竞技场的幸运排名记录
    example :  

    type    : Hash
    key_name: HASH_ARENA_EXCHANGE
    format  : key_name cid marshal.dumps([exchange_data, ...])
    others  : exchange_data=[update_time, exchange_id, total_count, daily_count]
    used to : 竞技场中的兑换记录 
    example :  

    type    : Hash
    key_name: HASH_MYSTICAL_SHOP 
    format  : key_name cid marshal.dumps(detail)
    others  : detail = [last_time, free_count, max_count, mystical_items, had_refresh]
            mystical_items = Array(Array(index, item_type, item_id, item_num, cost_item_type, cost_itemID, cost_itemNum, exchange_count), ...),
            had_refresh: 当天已刷新的次数
    used to : 神秘商店 道具 
    example :  

    type    : Hash
    key_name: HASH_MYSTICAL_LOTTERY 
    format  : key_name cid marshal.dumps(data) cid marshal.dumps(data) ... 
    others  : data = [(role_lvl, vip_lvl), {id: count, id: count}]
    used to : 神秘商店 随机八个道具 并记录未被抽中的次数 抽中后归零
    example :  

    type    : Hash
    key_name: HASH_EAT_PEACH 
    format  : key_name cid last_end_time cid last_end_time ... 
    others  : 
    used to : 精彩活动 吃桃 并记录上次吃桃的时间
    example : 

    type    : Hash
    key_name: HASH_EAT_PEACH_REWARD 
    format  : key_name cid status get_time 
    others  : 是否随出奖励， 随出的时间
    used to : 精彩活动 吃桃奖励 记录是否随出奖励
    example :  

    type    : Hash
    key_name: HASH_MONTHLY_CARD HASH_DUAL_MONTHLY_CARD 
    format  : key_name cid last_reward_time cid marshal.dumps([last_reward_time, prev_reward_time]) ... 
    others  : prev_reward_time-可补领的时间点
    used to : 精彩活动 月卡奖励 并记录上次领奖的时间
    example :  

    type    : Hash
    key_name: HASH_GROWTH_PLAN_REWAED 
    format  : key_name cid marshal.dumps(reward_level) cid marshal.dumps(reward_level) ... 
    others  : reward_level=[plan_level, ...]
    used to : 精彩活动 成长计划 记录已领取奖励的等级
    example :  

    type    : Hash
    key_name: HASH_BUY_GROW_PLAN_TOTAL_NUM
    format  : key_name cid marshal.dumps([total, status] 
    others  : 全服购买总人数， 是否领取，0-不能领取，1-可以领取，未领取，2-已领取
    used to : 精彩活动 成长计划
    example : 


    type    : Hash
    key_name: HASH_VIP_WELFARE_REWARD 
    format  : key_name cid last_reward_time cid last_reward_time ... 
    others  : 
    used to : 精彩活动 VIP福利奖励 并记录上次领奖的时间
    example :  

    type    : Hash
    key_name: HASH_PAY_ACTIVITY 
    format  : key_name cid marshal.dumps(data), ...
    others  : data = [had_award_ids, total_pay], 其中had_award_ids=[award_id, ...]
    used to : 精彩活动 累计充值详情 
    example :  

    type    : Hash
    key_name: HASH_CONSUME_ACTIVITY 
    format  : key_name cid marshal.dumps(data), ...
    others  : data = [had_award_ids, total_consume], 其中had_award_ids=[award_id, ...]
    used to : 精彩活动 累计消费详情
    example :  

    type    : Hash
    key_name: HASH_PAY_CREDITS_BACK
    format  : key_name cid total_credits ...
    others  : total_credits-累计返还的钻石数
    used to : 精彩活动 充值返利
    example : 

    type    : Hash
    key_name: HASH_LUCKY_TURNTABLE
    format  : key_name cid marshal.dumps(data), ...
    others  : data = {type: [last_lucky_time, last_reward_time], ...} 其中type-转盘档位, last_lucky_time-上次幸运一下的时间, last_reward_time-上次领奖的时间
    used to : 精彩活动 幸运转盘
    example : 

    type    : Hash
    key_name: HASH_AWARD_CENTER_cid
    format  : key_name award_id marshal.dumps(data) ...
    others  : award_type 1:首充奖励; 2:竞技场奖励; 3:扫荡天外天奖励, 4:未领的月卡奖励, 5:未领的VIP福利
              award_type=1时, data = [award_id, award_type, [award_time]]
              award_type=2时, data = [award_id, award_type, [award_time, arena_rank]]
              award_type=3时, data = [award_id, award_type, [award_time, [tower_layer]]]
              award_type=4时, data = [award_id, award_type, [award_time]]
              award_type=5时, data = [award_id, award_type, [award_time]]
    used to : 领奖中心的玩家奖励 
    example :  

    type    : Hash
    key_name: HASH_HINCRBY_KEY 
    format  : key_name AWARD_ID 1 
    others  :  
    used to :  
    example :  

    type    : Hash
    key_name: HASH_DUNGEON_DROP_RATE_dungeon_id
    format  : key_name cid marshal.dumps(data) ...
    others  : data = {drop_id: rate, ...}
    used to : 副本掉落概率计算, 添加后不能删除
    example :  

    type    : Hash
    key_name: HASH_SCENE_COOLDOWN_TIME 
    format  : key_name cid end_cooldown_time ...
    others  :  
    used to : 副本连续战斗的冷却截止时间
    example :  

    type    : Hash
    key_name: HASH_SCENE_RESET_DAILY 
    format  : key_name cid marshal.dumps(data) ...
    others  : data = [last_sweep_time, had_sweep, item_reset, credit_reset], 上次扫荡时间/已扫荡的次数/道具重置的次数/钻石重置的次数
    used to : 副本挑战次数重置/全扫荡的记录
    example :  

    type    : Hash
    key_name: HASH_SCENE_STAR_REWARDED 
    format  : key_name cid marshal.dumps(data) ...
    others  : data={scene_id: [star_count, ...], ...}
    used to : 副本星数奖励记录
    example :  

    type    : Hash
    key_name: HASH_ELITESCENE_PASSED
    format  : key_name cid marshal.dumps(data) ...
    others  : data = [elitescene_id, ...]
    used to : 精英副本已胜利的ID记录
    example : 

    type    : Hash
    key_name: HASH_SHRINE_TYPE_card_type
    format  : key_name cid marshal.dumps(data) ...
    others  : data = [shrine_level, rand_count, last_free_time, last_purple_time, first_blue, first_purple] 
    used to : 不同抽卡类型对应的抽卡池神坛等级、抽卡次数、上一次免费时间、上次获得紫卡的时间, 第一次使用钻石抽蓝卡/紫卡的标志位(0-已使用, 1-未使用) 等信息
    example :  

    type    : Hash
    key_name: HASH_VIP_PACKAGE_RECORD
    format  : key_name cid marshal.dumps(data) ...
    others  : data=[vip_level, ...] 
    used to : VIP礼包的购买记录 
    example :  

    type    : Hash
    key_name: HASH_LOGIN_PACKAGE 
    format  : key_name cid marshal.dumps(data) ...
    others  : data=[last_login_timestamp, had_package_id]
    used to : 领取登录礼包的信息
    example :  

    type    : Hash
    key_name: HASH_PAY_LOGIN_PACKAGE
    format  : key_name cid marshal.dumps(data) ...
    others  : data=[last_pay_login_timestamp, package_id, status], package_id-可签到的最大的豪华礼包ID, status-0:未领,1:已领。
    used to : 领取豪华登录礼包的信息
    example :  

    type    : Hash
    key_name: HASH_LEVEL_PACKAGE 
    format  : key_name cid marshal.dumps(data) ...
    others  : data = [level, ...]
    used to : 已领取的等级礼包
    example :  

    type    : Hash
    key_name: HASH_OPENSERVICE_PACKAGE 
    format  : key_name cid marshal.dumps(data) ...
    others  : data=[last_login_timestamp, [got_package_id, ...], max_got_package_id], max_got_package_id-可领取的最大礼包ID
    used to : 已领取的开服礼包的记录
    example :  

    type    : Hash
    key_name: HASH_ONLINE_PACKAGE
    format  : key_name cid marshal.dumps(data)
    others  : data=[cur_group, cur_package_id, next_timestamp, last_timestamp, group_count]
    used to : 未领取的在线礼包的记录 
    example : 

    type    : Hash
    key_name: HASH_RANDOM_CHEST_chest_id
    format  : key_name cid marshal.dumps(data)
    others  : data= {id:extra_rate, ...}
    used to : 开宝箱随机道具时的额外权重 
    example :  

    type    : Hash
    key_name: HASH_TREASURE_CHARACTER_CAMP
    format  : key_name cid marshal.dumps(data) cid marshal.dumps(data) ...
    others  : data = get_player_camp
    used to : 夺宝中满足宝物碎片被抢夺条件的玩家的阵容
    example : 已删除

    type    : Hash
    key_name: HASH_TREASURE_CHARACTER_IDS
    format  : key_name cid marshal.dumps(data) cid marshal.dumps(data) ...
    others  : data = [treasure_id, ...]
    used to : 夺宝中玩家拥有可被抢夺的碎片对应的宝物ID列表
    example : 已删除

    type    : Hash
    key_name: TPL_TREASURE_SHARD_GOT_shard_id
    format  : key_name cid marshal.dumps(data) ...
    others  : data = (cid, user_level, nick_name)
    used to : 夺宝中碎片对应的可被抢夺的玩家信息
    example :  

    type    : Hash
    key_name: HASH_TREASURESHARD_ROBOT_RATE_shard_id
    format  : key_name cid data
    others  :  
    used to : 夺宝中玩家错失该碎片的累计概率
    example :  

    type    : Hash
    key_name: HASH_AVOID_WAR_TIME 
    format  :  
    others  :  
    used to :  
    example :  

    type    : Hash
    key_name: HASH_MAIL_CONTENT_type_cid
    format  : key_name primary marshal.dumps(data)
    others  : data = (primary, send_time, type, module_id, detail), detail详见协议17.2, primary是自增长 MAIL_PRIMARY_INC
    used to : 记录邮件内容 
    example :  

    type    : Hash
    key_name: HASH_FRIENDS_SEND_DOUZHAN
    format  : key_name cid marshal.dumps(data) ...
    others  : data = (timestamp, [cid, ...])
    used to : 记录玩家已赠送的斗战点的信息
    example :  

    type    : Hash
    key_name: HASH_FRIENDS_GIFT_DOUZHAN_cid
    format  : key_name send_cid marshal.dumps(data)
    others  : data = (send_cid, lead_id, nick_name, level, might), 
            同时还包含FRIENDS_DOUZHAN_GET marshal.dumps((timestamp, count))记录当天已领的次数
    used to : 玩家的好友赠送的斗战点的信息 
    example :  

    type    : Hash
    key_name: HASH_ALLIANCE_INFO
    format  : key_name alliance_id marshal.dumps(data)
    others  : data = (alliance_id, name, level, exp, description, members, notice)
    used to : 仙盟基本信息
    example :  

    type    : Hash
    key_name: HASH_ALLIANCE_MEMBER
    format  : key_name cid marshal.dumps(data)
    others  : data = (cid, name, lead_id, level, vip_level, might, rank, logoff_time, position, contribution, contribution_total, cd_time)
    used to : 玩家的基本信息
    example :  

    type    : Hash
    key_name: HASH_ALLIANCE_LEVEL
    format  : key_name alliance_id marshal.dumps(data)
    others  : data = [sacrifice_level, shop_level, scene_level, task_hall_level]
    used to : 仙盟的建筑等级信息
    example : 

    type    : Hash
    key_name: HASH_ALLIANCE_HALL
    format  : key_name alliance_id marshal.dumps(data)
    others  : data = [last_timestamp, [[nick_name, contribution_id], ...], [cid, ...]]
    used to : data[0]-上一次大殿建设时间点, data[1]-当天已完成建设的详情, data[2]-当日已完成建设的玩家ID列表
    example : 仙盟大殿的基本信息

    type    : Hash
    key_name: HASH_ALLIANCE_SACRIFICE
    format  : key_name alliance_id marshal.dumps(data)
    others  : data = [last_timestamp, total_count, [[cid, contribution_count, credits_count], ...]]
    used to : last_timestamp-上一次仙盟成员拜祭女娲的时间点, contribution_count-当天已完成贡献点拜祭的次数, credits_count-当天已完成拜祭的仙盟成员信息
    example : 仙盟女蜗宫的基本信息

    type    : Hash
    key_name: HASH_ALLIANCE_LIMIT_ITEM_RANDOM
    format  : key_name alliance_id marshal.dumps(data)
    others  : data = [alliance_level, {shop_item_id: count, ...}]
    used to : 仙盟商店中的珍宝信息 随机三个珍宝 并记录未被抽中的次数 抽中后归零
    example : 

    type    : Hash
    key_name: HASH_ALLIANCE_LIMIT_ITEM
    format  : key_name alliance_id marshal.dumps(data)
    others  : data = [last_refresh_time, [[shop_item_id, [cid, ...]], ...]]
    used to : last_refresh_time-上一次仙盟珍宝刷新的时间点, cid-当天已兑换该珍宝的玩家ID
    example : 仙盟商店的珍宝信息

    type    : Hash
    key_name: HASH_ALLIANCE_ITEM
    format  : key_name cid marshal.dumps(data)
    others  : data = [last_refresh_time, [[shop_item_id, count],...]]
    used to : shop_item_id-仙盟商城中的商城道具ID, count-当天已兑换的道具次数
    example : 仙盟商店的普通道具信息

    type    : Hash
    key_name: LIST_ALLIANCE_REQUEST_alliance_id
    format  : key_name marshal.dumps(data)
    others  : data = [cid, name, level, lead_id, might, rank, request_time]
    used to : 仙盟请求的信息
    example :  

    type    : Hash
    key_name: HASH_ALLIANCE_MESSAGES
    format  : key_name alliance_id marshal.dumps(data)
    others  : data = [[timestamp, cid, content], ...]
    used to : 仙盟留言板
    example : 

    type    : Hash
    key_name: 
    format  : 
    others  : 
    used to : 
    example : 

    type    : Hash
    key_name: 
    format  : 
    others  : 
    used to : 
    example : 

    type    : Hash
    key_name: HASH_LIMIT_FELLOW_SHRINE
    format  : key_name cid marshal.dumps(data) ...
    others  : data = [activity_id, shrine_level, rand_count, last_free_time] 
    used to : 限时神将的活动ID、抽卡池神坛等级、抽卡次数、上一次免费时间
    example :  

    type    : Sorted Set
    key_name: SET_LIMIT_FELLOW_NAME_SCORE
    format  : key_name score nick_name score nick_name ...
    others  : 
    used to : 限时神将中的积分排行榜 
    example :  

    type    : Hash
    key_name: HASH_ATLASLIST_AWARD 
    format  : key_name cid marshal.dumps(data) ...
    others  : data = [(category_id, second_type, start_level), ...]
    used to : 图鉴星级收齐后的领奖记录
    example :  

    type    : Hash
    key_name: HASH_SERVER_FORBIDDEN
    format  : key_name cid end_timestamp ...
    others  : end_timestamp-封号的截止时间 -1:永久封号 0:未封号
    used to : 被封号的玩家信息
    example : 

    type    : Hash
    key_name: HASH_SERVER_MUTE
    format  : key_name cid end_timestamp ...
    others  : end_timestamp-禁言的截止时间 -1:永久禁言 0:未禁言
    used to : 
    example : 

    type    : Hash
    key_name: HASH_GM_GRANT_ITEMS
    format  : key_name grant_key marshal.dumps(((cids, items_list, expire_ts), ...))
    others  : cids-[]为全服玩家, expire_ts-奖励的过期时间
    used to : GM发放道具的记录
    example : 

    type    : Hash
    key_name: SET_GOT_GRANT_KEYS_cid
    format  : key_name [grant_key, ...]
    others  : 
    used to : 玩家领取的GM奖励
    example : 

    type    : Hash
    key_name: HASH_DAILY_QUEST
    format  : key_name cid marshal.dumps( (last_timestamp, had_reward, quest_info, total_score) ), 
            其中last_timestamp:上一次每日任务的时间点。had_reward=[reward_id, ...], quest_info=[[quest_id, quest_status, count], ...], quest_id:任务ID。quest_status:任务状态,0-未完成 1-已完成,未领取 2-已完成，已领取。count:任务已做的次数。total_score:总积分。当quest_status=0时, count值才有效。
    others  : 
    used to : 每日任务的详情
    example : 

    type    : Hash
    key_name: HASH_JOUST_INFO
    format  : key_name cid marshal.dumps( [last_timestamp, had_count, had_buy, [cid, cid, cid], total_buy] ),
             其中 last_timestamp:上一次大乱斗的时间点, had_count:已使用的免费挑战次数, had_buy:剩余的已购买挑战次数, total_buy:今日已购买的挑战次数, cid:依次为上左右的玩家CID, 其中1-5000为机器人ID
    others  : 
    used to : 大乱斗中玩家的基本信息
    example : 

    type    : Sorted Set
    key_name: SET_JOUST_CID_SCORE
    format  : key_name score cid score cid ... ...
    others  : 
    used to : 大乱斗中玩家的积分排行榜 
    example : 

    type    : Hash
    key_name: HASH_JOUST_ENEMY_INFO
    format  : key_name cid marshal.dumps( [last_timestamp, [cid, cid, ...]] ) ... ...
    others  : 
    used to : 大乱斗中玩家的仇敌列表
    example : 

    type    : Hash
    key_name: HASH_JOUST_HONOR_EXCHANGE
    format  : key_name cid marshal.dumps( [[last_timestamp, exchange_id, total_had_count, week_had_count, daily_had_count], ...] )
            其中last_timestamp:上一次兑换的时间点, exchange_id:兑换ID,唯一标识一个道具, total_had_count:总计已兑换的次数, week_had_count:每周已兑换的次数, daily_had_count:每日已兑换的次数
    others  : 
    used to : 大乱斗中玩家的兑换记录
    example : 

    type    : Sorted Set
    key_name: SET_JOUST_CID_RANK
    format  : key_name rank cid rank cid ... ...
    others  : 
    used to : 上一次大乱斗中的排行榜前十名
    example : 

    type    : Hash
    key_name: HASH_DAILY_PAY_RECORD
    format  : key_name pay_date marshal.dumps( [[cid, total_cost], ...] )
    others  : pay_date:充值日期, 如2015-01-30。cid:玩家ID。total_cost:pay_date当天充值总额。
    used to : 玩家每日充值记录
    example : 

    type    : Hash
    key_name: DICT_LOVER_KISS 
    format  : key_name cid marshall.dumps([normal_rose, blue_rose, extra_blue_rose, last_opened_t, opened_num, opened_list])
    others  :普通玫瑰，蓝色玫瑰，额外获得的蓝色玫瑰，上次获得普通玫瑰时间，感动美女数量，感动列表 
    used to : 
    example : 

    type    : Sorted Set
    key_name: SET_SCENE_CID_STAR
    format  : key_name star cid star cid ... ...
    others  : star-玩家的总副本星数, cid-玩家ID
    used to : 剧情副本的排行榜
    example : 

    type    : Sorted Set
    key_name: SET_CLIMBING_CID_LAYER
    format  : key_name layer cid layer cid ... ...
    others  : layer-玩家天外天中的最大塔层, cid-玩家ID
    used to : 天外天的排行榜
    example : 

    type    : Hash
    key_name: DICT_DIG_TREASURE_INFO 
    format  : free_dig_count, total_dig_count, last_free_time
    others  : 免费次数， 总次数， 上次免费回复时间
    used to : 皇陵探宝
    example : 

    type    : Hash
    key_name: HASH_BROADCAST_MESSAGES
    format  : key_name id content id content ... ...
    others  : 
    used to : OSS 走马灯配置
    example : 

    type    : Hash
    key_name: DICT_GROUP_BUY_INFO
    format  : buy_type: buy_num
    others  : 购买档次，购买人数
    used to : 限时团购
    example : 

    type    : Hash
    key_name: DICT_GROUP_BUY_PERSON_INFO
    format  : cid:[[buy_count,[get_status, get_status2,..]],] 
    others  : 购买次数，领取状态
    used to : 限时团购
    example : 

    type    : Hash
    key_name: HASH_CAMPRAND_COMMON 
    format  : key_name CAMPRAND data1 cid data2 ... ...
    others  : field=CAMPRAND时, value=marshal.dumps([next_reset_timestamp, curr_group]); field=cid时, value=marshal.dumps([last_reward_timestamp, [[curr_group, had_randcard_count], [curr_group, had_randcard_count]], [[next_group, 0], [next_group, 0]])
    used to : 阵营抽卡记录
    example : 

    type    : Hash
    key_name: HASH_OPEN_SERVER_INFO
    format  : cid: dumps(_data, _shop_data)
    others  : _data:{1:[[quest_id, status, value],...]}
    used to : 任务id， 状态0-未完成，1-未领取，2-已领取， 完成值
    example : 

    type    : Hash
    key_name: HASH_ACHIEVEMENT_INFO 
    format  : cid:dumps(_data)
    others  : _data: {type:{id:[status, value],..},..}
    used to : type:成就类型，id成就id，status完成状态。 value 完成度
    example : 

    type    : Hash
    key_name: 
    format  : 
    others  : 
    used to : 
    example : 


'''







