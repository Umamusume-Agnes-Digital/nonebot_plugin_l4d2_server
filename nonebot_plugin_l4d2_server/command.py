from nonebot import on_notice,on_command,on_regex,on_fullmatch,on_shell_command,on_keyword

import re
import nonebot
from nonebot.permission import SUPERUSER
from nonebot.typing import T_Handler,T_State
from nonebot.adapters.onebot.v11 import (
    GroupUploadNoticeEvent,
    NoticeEvent,
    Bot,
    MessageEvent,
    Message,
    MessageSegment,
    GroupMessageEvent,
    PrivateMessageEvent
    )
from .l4d2_anne.server import server_key,ANNE_IP
from .config import Master,ADMINISTRATOR,reMaster,file_format

help_ = on_command('l4_help',aliases={'求生帮助'},priority=20,block=True)

# 服务器
# last_operation_time = nonebot.Config.parse_obj(nonebot.get_driver().config.dict()).SUPERUSERS



def wenjian(
event:NoticeEvent):
    superuse = nonebot.get_driver().config.l4_master
    args = event.dict()
    try:
        name: str = args['file']['name']
        usr_id = str(args['user_id'])
    except KeyError:
        return False
    if args['notice_type'] == 'offline_file':
        if superuse:
            return name.endswith(file_format) and usr_id in superuse
        else:
            return name.endswith(file_format)
    elif args['notice_type'] == 'group_upload':
        if superuse:
            return usr_id in superuse and name.endswith(file_format)
        else:
            return False

up = on_notice(rule=wenjian)



rename_vpk = on_regex(
        r"^求生地图\s*(\S+.*?)\s*(改|改名)?\s*(\S+.*?)\s*$",
    flags=  re.S,
    block= True,
    priority= 20,
    permission= Master,
)

find_vpk = on_command("l4_map",aliases={"求生地图","查看求生地图"},priority=25,block=True)
del_vpk = on_command("l4_del_map",aliases={"求生地图删除","地图删除"},priority=20,block=True,permission= Master)
rcon_to_server = on_command('rcon',aliases={"求生服务器指令","服务器指令","求生服务器控制台"},block=True,permission= Master)
check_path = on_command('l4_check',aliases={'求生路径'},priority=20,block=True,permission= Master)
smx_file = on_command('l4_smx',aliases={'求生插件'},priority=20,block=True,permission= Master)

# anne
anne_player = on_command('Ranne',aliases={"求生anne"},priority=25,block=True)
anne_bind = on_command('Rbind',aliases={'steam绑定','求生绑定','anne绑定'},priority=20,block=True)
del_bind = on_command('del_bind',aliases={'steam解绑','求生解绑','anne解绑'},priority=20,block=True)
read_ip = on_command('anne',aliases={'求生云服'},priority=20,block=True)
prison = on_command('zl',aliases={'坐牢'},priority=20,block=True)
open_prison = on_command('kl',aliases={'开牢'},priority=20,block=True)

updata = on_command('updata',aliases={'求生更新'},priority=20,block=True,permission= Master)
get_ip = on_command('114514919181',aliases=server_key(),priority=80,block=True)
def reload_ip():
    global updata,get_ip
    updata = on_command('updata',aliases={'求生更新'},priority=20,block=True,permission= Master)
    get_ip = on_command('114514919181',aliases=server_key(),priority=80,block=True)
tan_jian = on_command('tj',aliases={'探监'},priority=20,block=True)

# 查询
queries = on_command('queries',aliases={'求生ip','求生IP'},priority=20,block=True)
add_queries = on_command('addq',aliases={"求生添加订阅"},priority=20,block=True,permission= Master)
del_queries = on_command('delq',aliases={"求生取消订阅"},priority=20,block=True,permission= Master)
show_queries = on_command('showq',aliases={"求生订阅"},priority=20,block=True)
join_server = on_command('showq',aliases={"求生加入"},priority=20,block=True)
connect_rcon = on_command("Rrcon", aliases={"求生连接", '求生链接','求生rcon'}, priority=50, block=False)
end_connect = ['stop', '结束', '连接结束', '结束连接']
search_api = on_command('search',aliases={'求生三方'}, priority=20, block=True,permission= Master)
which_map = on_keyword(("是什么图"),priority=20, block=False)

# 下载内容
up_workshop = on_command('workshop',aliases={'创意工坊下载','求生创意工坊'},priority=20,block=True)
vtf_make = on_command('vtf_make',aliases={'求生喷漆'},priority=20,block=True)

@help_.handle()
async def _():
    msg = [
        '=====求生机器人帮助=====',
        '1、电信服战绩查询【求生anne[id/steamid/@]】',
        '2、电信服绑定【求生绑定[id/steamid]】',
        '3、电信服状态查询【云xx】'
        '4、创意工坊下载【创意工坊下载[物品id/链接]】',
        '5、指定ip查询【求生ip[ip]】(可以是域名)',
        '6、求生喷漆制作【求生喷漆】',
        '6、本地服务器操作(略，详情看项目地址)',
    ]
    messgae = ''
    for i in msg:
        messgae += i + '\n'
    await help_.finish(messgae)

def get_session_id(event: MessageEvent) -> str:
    if isinstance(event, GroupMessageEvent):
        return f"group_{event.group_id}"
    else:
        return f"private_{event.user_id}"
