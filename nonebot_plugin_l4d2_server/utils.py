from zipfile import ZipFile
from nonebot.adapters.onebot.v11 import Bot,MessageEvent,GroupMessageEvent
from nonebot.log import logger
import struct
import httpx
import os
try:
    import py7zr
except:
    pass
from pathlib import Path
from PIL import Image
from .txt_to_img import txt_to_img
from .config import *
from .l4d2_anne import write_player,del_player,anne_messgae
from .l4d2_server.rcon import read_server_cfg_rcon,rcon_server
from .l4d2_queries import queries,player_queries
from .l4d2_queries.qqgroup import *
from .l4d2_server.workshop import workshop_to_dict
from .l4d2_queries.ohter import ANNE_HOST
from .l4d2_image.steam import url_to_byte
import tempfile
import random


async def get_file(url:str,down_file:Path):
    '''
    下载指定Url到指定位置
    '''
    try:
        maps = await url_to_byte(url)
        if maps == None:
            print('没有数据啊')
            mes = None
        logger.info('已获取文件，尝试新建文件并写入')
        with open(down_file ,'wb') as mfile:
            mfile.write(maps)
            logger.info('下载成功')
            mes ='文件已下载,正在解压'
    except Exception as e:
        print(e)
        logger.info("文件获取不到/已损坏")
        mes = None
    return mes

def get_vpk(vpk_list:list,path):
    '''
    获取所有vpk文件
    '''
    for file in os.listdir(path):
        if file.endswith('.vpk'):
            vpk_list.append(file)
    return vpk_list

def mes_list(mes:str,name_list:list):
    n = 0
    if name_list:
        for i in name_list:
            n += 1
            mes += "\n" + str(n) + "、" + i
    return mes

def support_gbk(zip_file: ZipFile):
    '''
    压缩包中文恢复
    '''
    name_to_info = zip_file.NameToInfo
    # copy map first
    for name, info in name_to_info.copy().items():
        real_name = name.encode('cp437').decode('gbk')
        if real_name != name:
            info.filename = real_name
            del name_to_info[name]
            name_to_info[real_name] = info
    return zip_file

def del_map(num,map_path):
    '''
    删除指定的地图
    '''
    vpk_list = []
    map = get_vpk(vpk_list,map_path)
    map_name = map[int(num)-1]
    del_file = Path(map_path,map_name)
    os.remove(del_file)
    return map_name

def rename_map(num,rename,map_path):
    '''
    改名指定的地图
    '''
    vpk_list = []
    name = str(rename)
    map = get_vpk(vpk_list,map_path)
    map_name = map[int(num)-1]
    old_file = Path(map_path,map_name)
    new_file = Path(map_path,name)
    os.rename(old_file,new_file)
    logger.info('改名成功')
    return map_name

def text_to_png(msg: str) -> bytes:
    """文字转png"""
    return txt_to_img(msg)

def open_packet(name,down_file):
    """解压压缩包"""
    zip_dir = os.path.dirname(down_file)
    logger.info('文件名为：' + name)
    if name.endswith('.zip'):
        mes = 'zip文件已下载,正在解压'
        with support_gbk(ZipFile(down_file, 'r')) as zip_ref:
            zip_ref.extractall(zip_dir)
        os.remove(down_file)
    elif name.endswith('.7z'):
        mes ='7z文件已下载,正在解压'
        with py7zr.SevenZipFile(down_file, 'r') as z:
            z.extractall(map_path)
        os.remove(down_file)
    elif name.endswith('.vpk'):
        mes ='vpk文件已下载'
    return mes

def solve(msg:str):
    """删除str最后一行"""
    lines = msg.splitlines()
    lines.pop()
    return '\n'.join(lines)


async def search_anne(name:str,usr_id:str):
    """获取anne成绩"""
    msg = await anne_messgae(name,usr_id)
    if type(msg) == str:
        msg = solve(msg)
    return msg
    

async def bind_steam(id:str,msg:str,nickname:str):
    """绑定qq-steam"""
    return await write_player(id,msg,nickname)

def name_exist(id:str):
    """删除绑定信息"""
    return del_player(id)

async def get_message_at(data: str) -> list:
    '''
    获取at列表
    :param data: event.json()
    抄的groupmate_waifu
    '''
    qq_list = []
    data = json.loads(data)
    try:
        for msg in data['message']:
            if msg['type'] == 'at':
                qq_list.append(int(msg['data']['qq']))
        return qq_list
    except Exception:
        return []
    

def at_to_usrid(at):
    """at对象变qqid否则返回usr_id"""
    if at != []:
        if at and at[0] != usr_id:
            at:str = at[0]
        usr_id:str = at
        return usr_id
    else:
        return None

async def command_server(msg:str):
    """rcon控制台返回信息"""
    logger.info(cfg_server)
    rcon = await read_server_cfg_rcon()
    logger.info([msg,l4_host,l4_port,rcon])
    msg = await rcon_server(rcon,msg)
    logger.info(msg)
    if len(msg)==0:
        msg = '你可能发送了一个无用指令，或者换图导致服务器无响应'
    if msg.startswith('Unknown command'):
        msg = msg.replace('Unknown command','').strip()
        msg = '无效指令：' + msg
    msg = msg.strip()
    return msg



async def queries_server(msg:list) -> str:
    """查询ip返回信息"""
    print(msg)
    ip = msg[0]
    port = msg[1]
    try:
        msgs = await  queries(ip,port)
    except TypeError:
        msgs = '服务器无响应'
        return msgs
    try:
        msgs += await player_queries(ip,port)
    except (KeyError,struct.error):
        pass
    return msgs

async def add_ip(group_id,host,port):
    """先查找是否存在，如果不存在则创建"""
    return await bind_group_ip(group_id,host,port)

async def del_ip(group_id,number):
    """删除群ip"""
    return await del_group_ip(group_id,number)

async def show_ip(group_id):
    """先查找群ip，再根据群ip返回"""
    data_list = await get_qqgroup_ip_msg(group_id)
    logger.info(data_list)
    if len(data_list) == 0 :
        return "本群没有订阅"
    msg = await qq_ip_queries_pic(data_list)
    if type(msg) == str:
        msg = solve(msg)
    return  msg

async def get_number_url(number):
    'connect AGNES.DIGITAL.LINE.PM:40001'
    ip = await get_server_ip(number)
    if not ip:
        return '该序号不存在'
    url = f'connect {ip}'
    return url

async def workshop_msg(msg:str):
    """url变成id，拼接post请求"""
    if msg.startswith('https://steamcommunity.com/sharedfiles/filedetails/?id'):
        try:
            msg = msg.split('&')[0]
        except:
            pass
        msg = msg.replace('https://steamcommunity.com/sharedfiles/filedetails/?id=','')
    if msg.isdigit():
        data:dict = await workshop_to_dict(msg)
        return data
    else:
        return None
    
async def save_file(file:bytes,path_name):
    """保存文件"""
    with open(path_name,'w') as files:
        files.write(file)
        
async def get_anne_server_ip(ip):
    """输出查询ip"""
    host,port = split_maohao(ip)
    data = await queries_server([host,port])
    lines = data.splitlines()
    msg = '\n'.join(lines[1:])
    msg += '\nconnect ' + ip
    return msg

async def upload_file(bot: Bot, event: MessageEvent, file_data: memoryview, filename: str):
    """上传临时文件"""
    with tempfile.NamedTemporaryFile("wb+") as f:
        f.write(file_data)
        if isinstance(event, GroupMessageEvent):
            await bot.call_api(
                "upload_group_file", group_id=event.group_id, file=f.name, name=filename
            )
        else:
            await bot.call_api(
                "upload_private_file", user_id=event.user_id, file=f.name, name=filename
            )

async def json_server_to_tag_dict(key:str,msg:str):
    """
    l4d2字典转tag的dict结果
     - 1、先匹配腐竹
     - 2、再匹配模式、没有参数则从直接匹配最上面的
     - 3、匹配数字（几服），没有参数则从结果里随机返回一个
    """
    data_dict = {}
    data_list = []
    msg = msg.replace(' ','')
    n = 0
    # 腐竹循环
    for tag,value in ANNE_HOST.items():
        value:list[dict]  
        if tag == key:
            data_dict.update({'server':tag})
            n = 1
            if msg == '':
                # 腐竹
                data_dict.update(random.choice(value))
            # 腐竹 + 序号
            elif msg.isdigit():
                for server in value:
                    if msg == str(server['id']):
                        data_dict.update(server)
            else:
                # 腐竹 + 模式 + 序号
                for server in value:
                    if msg.startswith(server['version']):
                        n = 2
                        data_list.append(server)
                        msg_id = msg[len(server['version']):]
                        if msg_id == str(server['id']):
                            n = 3
                            data_dict.update(server)
                if n == 2:
                    # 腐竹 + 模式
                    data_dict.update(random.choice(data_list))
    logger.info(data_dict)
    return data_dict