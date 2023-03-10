import datetime
from typing import Optional, Union

from fastapi import FastAPI
from fastapi import Header, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from jose import jwt
from nonebot import get_bot, get_app
from pydantic import BaseModel
from typing import List, Dict
from pathlib import Path

from pydantic import BaseModel, Field

from nonebot import get_driver, logger
from ruamel import yaml

CONFIG_PATH = Path() / 'data' / 'L4D2' / 'l4d2.yml'
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

driver = get_driver()

from .webUI import login_page, admin_app

requestAdaptor = '''
requestAdaptor(api) {
    api.headers["token"] = localStorage.getItem("token");
    return api;
},
'''
responseAdaptor = '''
responseAdaptor(api, payload, query, request, response) {
    if (response.data.detail == '登录验证失败或已失效，请重新登录') {
        window.location.href = '/l4d2/login'
        window.localStorage.clear()
        window.sessionStorage.clear()
        window.alert('登录验证失败或已失效，请重新登录')
    }
    return payload
},
'''


def authentication():
    def inner(token: Optional[str] = Header(...)):
        try:
            payload = jwt.decode(token, config_manager.config.web_secret_key, algorithms='HS256')
            if not (username := payload.get('username')) or username != config_manager.config.web_username:
                raise HTTPException(status_code=400, detail='登录验证失败或已失效，请重新登录')
        except (jwt.JWTError, jwt.ExpiredSignatureError, AttributeError):
            raise HTTPException(status_code=400, detail='登录验证失败或已失效，请重新登录')

    return Depends(inner)


COMMAND_START = driver.config.command_start.copy()
if '' in COMMAND_START:
    COMMAND_START.remove('')


class ChatGroupConfig(BaseModel):
    enable: bool = Field(True, alias='是否启用求生功能')
    map_master: List[str] = Field([], alias='分群地图管理员')

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.__fields__:
                self.__setattr__(key, value)


class ChatConfig(BaseModel):
    total_enable: bool = Field(True, alias='是否全局启用求生功能')
    map_path: List(str) = Field([], alias='求生地图路径')
    server_host: List(str) = Field([], alias='求生服务器地址')
    server_port: List(str) = Field([], alias='求生服务器端口')
    server_password: List(str) = Field([], alias='求生服务器rcon密码')
    web_secret_key: str = Field('49c294d32f69b732ef6447c18379451ce1738922a75cd1d4812ef150318a2ed0',
                                alias='后台管理token密钥')
    map_master: List[str] = Field([], alias='求生地图全局管理员qq')
    only_download:bool = Field(False, alias='下载地图是是否阻碍其他指令')
    api_token: str = Field('', alias='api的token')
    group_config: Dict[int, ChatGroupConfig] = Field({}, alias='分群配置')

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.__fields__:
                self.__setattr__(key, value)
                
class ChatConfigManager:

    def __init__(self):
        self.file_path = CONFIG_PATH
        if self.file_path.exists():
            self.config = ChatConfig.parse_obj(
                yaml.load(self.file_path.read_text(encoding='utf-8'), Loader=yaml.Loader))
        else:
            self.config = ChatConfig()
        self.save()

    def get_group_config(self, group_id: int) -> ChatGroupConfig:
        if group_id not in self.config.group_config:
            self.config.group_config[group_id] = ChatGroupConfig()
            self.save()
        return self.config.group_config[group_id]

    @property
    def config_list(self) -> List[str]:
        return list(self.config.dict(by_alias=True).keys())

    def save(self):
        with self.file_path.open('w', encoding='utf-8') as f:
            yaml.dump(
                self.config.dict(by_alias=True),
                f,
                indent=2,
                Dumper=yaml.RoundTripDumper,
                allow_unicode=True)
            
config_manager = ChatConfigManager()

class UserModel(BaseModel):
    username: str
    password: str


@driver.on_startup
async def init_web():
    if not config_manager.config.enable_web:
        return
    app: FastAPI = get_app()

    @app.post('/l4d2/api/login', response_class=JSONResponse)
    async def login(user: UserModel):
        if user.username != config_manager.config.web_username or user.password != config_manager.config.web_password:
            return {
                'status': -100,
                'msg':    '登录失败，请确认用户ID和密码无误'
            }
        token = jwt.encode({'username': user.username,
                            'exp':      datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
                                minutes=30)}, config_manager.config.web_secret_key, algorithm='HS256')
        return {
            'status': 0,
            'msg':    '登录成功',
            'data':   {
                'token': token
            }
        }

    @app.get('/l4d2/api/get_group_list', response_class=JSONResponse, dependencies=[authentication()])
    async def get_group_list_api():
        try:
            group_list = await get_bot().get_group_list()
            group_list = [{'label': f'{group["group_name"]}({group["group_id"]})', 'value': group['group_id']} for group
                          in group_list]
            return {
                'status': 0,
                'msg':    'ok',
                'data':   {
                    'group_list': group_list
                }
            }
        except ValueError:
            return {
                'status': -100,
                'msg':    '获取群和好友列表失败，请确认已连接GOCQ'
            }

    @app.get('/l4d2/api/chat_global_config', response_class=JSONResponse, dependencies=[authentication()])
    async def get_chat_global_config():
        try:
            bot = get_bot()
            groups = await bot.get_group_list()
            member_list = []
            for group in groups:
                members = await bot.get_group_member_list(group_id=group['group_id'])
                member_list.extend(
                    [{'label': f'{member["nickname"] or member["card"]}({member["user_id"]})',
                      'value': member['user_id']}
                     for
                     member in members])
            config = config_manager.config.dict(exclude={'group_config'})
            config['member_list'] = member_list
            return config
        except ValueError:
            return {
                'status': -100,
                'msg':    '获取群和好友列表失败，请确认已连接GOCQ'
            }



    @app.get('/l4d2', response_class=RedirectResponse)
    async def redirect_page():
        return RedirectResponse('/l4d2/login')

    @app.get('/l4d2/login', response_class=HTMLResponse)
    async def login_page_app():
        return login_page.render(site_title='登录 | l4d2 后台管理',
                                 theme='ang')

    @app.get('/l4d2/admin', response_class=HTMLResponse)
    async def admin_page_app():
        return admin_app.render(site_title='l4d2-Chat 后台管理',
                                theme='ang',
                                requestAdaptor=requestAdaptor,
                                responseAdaptor=responseAdaptor)

