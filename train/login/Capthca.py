from io import BytesIO

from PIL import Image

from define.Const import TYPE_LOGIN_NORMAL_WAY, TYPE_LOGIN_OTHER_WAY
from define.UrlsConf import loginUrls
from net.NetUtils import EasyHttp
from train.login import damatuWeb
from utils import FileUtils
from utils.Log import Log
import sys
import re


class Captcha(object):
    __REPONSE_NORMAL_CDOE_SUCCESSFUL = '4'
    __REPONSE_OHTER_CDOE_SUCCESSFUL = '1'
    __CAPTCHA_PATH = 'captcha.jpg'

    def getCaptcha(self, type=TYPE_LOGIN_NORMAL_WAY):
        urlInfo = loginUrls['other']['captcha'] if type == TYPE_LOGIN_OTHER_WAY else loginUrls['normal']['captcha']
        Log.info('正在获取验证码..')
        return EasyHttp.send(urlInfo)

    def check(self, results, type=TYPE_LOGIN_NORMAL_WAY):
        if type == TYPE_LOGIN_OTHER_WAY:
            return self._checkRandCodeAnsyn(results)
        return self._captchaCheck(results)

    def _checkRandCodeAnsyn(self, results):
        formData = {
            'randCode': results,
            'rand': 'sjrand',
        }
        jsonRet = EasyHttp.send(loginUrls['other']['captchaCheck'], data=formData)
        print('checkRandCodeAnsyn: %s' % jsonRet)

        def verify(response):
            return response['status'] and Captcha.__REPONSE_OHTER_CDOE_SUCCESSFUL == response['data']['result']

        return verify(jsonRet)

    def _captchaCheck(self, results):
        data = {
            'answer': results,
            'login_site': 'E',
            'rand': 'sjrand',
        }
        jsonRet = EasyHttp.send(loginUrls['normal']['captchaCheck'], data=data)
        print('captchaCheck: %s' % jsonRet)

        def verify(response):
            return Captcha.__REPONSE_NORMAL_CDOE_SUCCESSFUL == response[
                'result_code'] if 'result_code' in response else False

        return verify(jsonRet)

    def verifyCaptchaByClound(self, type=TYPE_LOGIN_NORMAL_WAY):
        captchaContent = self.getCaptcha(type)
        if captchaContent:
            FileUtils.saveBinary(Captcha.__CAPTCHA_PATH, captchaContent)
        else:
            Log.error('failed to save captcha')
            return None
        results = damatuWeb.verify(Captcha.__CAPTCHA_PATH)
        results = self.__cloundTransCaptchaResults(results)
        Log.info('captchaResult: %s' % results)
        return results, self.check(results)

    def verifyCaptchaByHand(self, type=TYPE_LOGIN_NORMAL_WAY):
        img = Image.open(BytesIO(self.getCaptcha(type)))
        if sys.platform == 'linux':
            img.save('12306.jpg', 'jpeg')
        else:
            img.show()
        Log.info(
            """ 
            -----------------
            | 1 | 2 | 3 | 4 |
            -----------------
            | 5 | 6 | 7 | 8 |
            ----------------- """)
        results = input("输入验证码索引(见上图，以'[,，；; ]'分割）: ")
        img.close()
        results = self.__indexTransCaptchaResults(results)
        Log.info('captchaResult: %s' % results)
        return results, self.check(results, type)

    def __indexTransCaptchaResults(self, indexes):
        coordinates = ['40,40', '110,40', '180,40', '250,40', '40,110', '110,110', '180,110', '250,110']
        results = []
        split = re.split(r'[\s+\,\;\，\；]', indexes)
        for index in split:
            results.append(coordinates[int(index)-1])
        return ','.join(results)

    def __cloundTransCaptchaResults(self, results):
        if type(results) != str:
            return ''
        offsetY = 30
        results = results.replace(r'|', r',').split(r',')
        for index in range(0, len(results)):
            if index % 2 != 0:
                results[index] = str(int(results[index]) - offsetY)
        return ','.join(results)


if __name__ == '__main__':
    pass
