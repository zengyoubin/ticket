import time

from define.Const import TYPE_LOGIN_NORMAL_WAY, TYPE_LOGIN_OTHER_WAY
from define.UrlsConf import loginUrls
from net.NetUtils import EasyHttp
from train.login.Capthca import Captcha
from utils import Utils
from utils.Log import Log
from Configure import USER_PWD,USER_NAME


def loginLogic(func):
    def wrapper(*args, **kw):
        reslut = False
        msg = ''
        for count in range(3):
            reslut, msg = func(*args, **kw)
            if reslut:
                break
            Log.warning(msg)
        return reslut, msg

    return wrapper


class Login(object):
    __LOGIN_SUCCESS_RESULT_CODE = 0

    def _passportRedirect(self):
        params = {
            'redirect': '/otn/login/userLogin',
        }
        EasyHttp.send(self._urlInfo['userLoginRedirect'])

    def _userLogin(self):
        params = {
            '_json_att': '',
        }
        EasyHttp.send(self._urlInfo['userLogin'])

    def _uamtk(self):
        jsonRet = EasyHttp.send(self._urlInfo['uamtk'], data={'appid': 'otn'})

        def isSuccess(response):
            return response['result_code'] == 0 if 'result_code' in response else False

        return isSuccess(jsonRet), \
               jsonRet['result_message'] if 'result_message' in jsonRet else 'no result_message', \
               jsonRet['newapptk'] if 'newapptk' in jsonRet else 'no newapptk'

    def _uamauthclient(self, apptk):
        jsonRet = EasyHttp.send(self._urlInfo['uamauthclient'], data={'tk': apptk})
        print(jsonRet)

        def isSuccess(response):
            return response['result_code'] == 0 if response and 'result_code' in response else False

        return isSuccess(jsonRet), '%s:%s' % (jsonRet['username'], jsonRet['result_message']) if jsonRet \
            else 'uamauthclient failed'

    def login(self, userName, userPwd):
        # 登录有两种api
        for count in range(2):
            result, msg = self._login(userName, userPwd, type=(count % 2))
            if Utils.check(result, msg):
                return result, msg
        return False, '登录失败'

    @loginLogic
    def _login(self, userName, userPwd, type=TYPE_LOGIN_NORMAL_WAY):
        if type == TYPE_LOGIN_OTHER_WAY:
            self._urlInfo = loginUrls['other']
            return self._loginAsyncSuggest(userName, userPwd)
        self._urlInfo = loginUrls['normal']
        return self._loginNormal(userName, userPwd)

    def _loginNormal(self, userName, userPwd):
        self._init()
        self._uamtk()
        if not Captcha().verifyCaptchaByHand()[1]:
            return False, '验证码识别错误!'
        payload = {
            'username': userName,
            'password': userPwd,
            'appid': 'otn',
        }
        jsonRet = EasyHttp.send(self._urlInfo['login'], data=payload)

        def isLoginSuccess(responseJson):
            return 0 == responseJson['result_code'] if responseJson and 'result_code' in responseJson else False, \
                   responseJson[
                       'result_message'] if responseJson and 'result_message' in responseJson else 'login failed'

        result, msg = isLoginSuccess(jsonRet)
        if not result:
            return False, msg
        # self._userLogin()
        self._passportRedirect()
        result, msg, apptk = self._uamtk()
        if not Utils.check(result, msg):
            return False, 'uamtk failed'
        return self._uamauthclient(apptk)

    def _loginAsyncSuggest(self, userName, userPwd):
        self._init()
        results, verify = Captcha().verifyCaptchaByHand(type=TYPE_LOGIN_OTHER_WAY)
        if not verify:
            return False, '验证码识别错误!'
        formData = {
            'loginUserDTO.user_name': userName,
            'userDTO.password': userPwd,
            'randCode': results,
        }
        jsonRet = EasyHttp.send(self._urlInfo['login'], data=formData)
        print('loginAsyncSuggest: %s' % jsonRet)

        def isSuccess(response):
            return response['status'] and response['data']['loginCheck'] == 'Y' if 'data' in response else False, \
                   response['data']['otherMsg'] if 'data' in response else response['messages']

        loginSuccess, otherMsg = isSuccess(jsonRet)
        return loginSuccess, '%s:%s' % (userName, otherMsg or '登录成功!')

    def isLogin(self):
        formData = {
            '_json_att': ''
        }
        jsonRet = EasyHttp.send(self._urlInfo['checkUser'])
        Log.debug('checkUser: %s' % jsonRet)
        return jsonRet['data']['flag'] if jsonRet and 'data' in jsonRet and 'flag' in jsonRet[
            'data'] else False

    def loginOut(self):
        EasyHttp.send(self._urlInfo['loginOut'])
        self._init()
        return self._uamtk()

    def _init(self):
        EasyHttp.send(self._urlInfo['init'])


if __name__ == '__main__':
    login = Login()
    login.login(USER_NAME,USER_PWD)
    time.sleep(3)
    print(login.loginOut())
