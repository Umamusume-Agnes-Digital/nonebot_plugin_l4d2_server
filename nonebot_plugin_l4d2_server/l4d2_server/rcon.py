from rcon.source import rcon
import asyncio
from pathlib import Path
from ..config import l4_file,CHECK_FILE
from ..config import l4_rcon,l4_host,l4_port,l4_rcon


async def rcon_server(PASSWORD:str,msg:str):
    # response = await rcon(command=msg, host=l4_host, port=l4_port, passwd=PASSWORD,encoding='utf-8')
    # return response
    try:
        response = await asyncio.wait_for(rcon(command=msg, host=l4_host[CHECK_FILE], port=l4_port[CHECK_FILE], passwd=PASSWORD), timeout=30)
        return response
    except asyncio.TimeoutError:
        return '超时'

async def read_server_cfg_rcon():
    """如果没有输入rcon，尝试自动获取"""
    if not l4_rcon[CHECK_FILE]:
        cfg_server = Path(l4_file[CHECK_FILE],'left4dead2/cfg/server.cfg')
        with open(cfg_server,'r')as cfg:
            content:str = cfg.read()
            lines = content.split('\n')
            for line in lines:
                if line.startswith('rcon_password'):
                    password = line.split(' ')[-1]
                    password = password.strip('"')
                    return password
    return l4_rcon[CHECK_FILE]