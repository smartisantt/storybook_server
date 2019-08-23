# coding=utf-8
import requests,json,hashlib



class Express100(object):

    key = 'kPbvcXiq4745'  # 客户授权key
    customer = 'CDF754C6FC3227436872C39C31D40E25'  # 查询公司编号
    company_url = "http://www.kuaidi100.com/autonumber/auto"
    # trace_url = "http://www.kuaidi100.com/query"
    trace_url = 'http://poll.kuaidi100.com/poll/query.do'  # 实时查询请求地址

    @classmethod
    def get_json_data(cls, url, payload):
        r = requests.get(url=url, params=payload)
        return r.json()

    @classmethod
    def get_company_info(cls, express_code):
        payload = {"num": express_code, "key":cls.key}
        data = cls.get_json_data(cls.company_url, payload)
        return data

    @classmethod
    def get_express_info(cls, express_code):
        company_info = cls.get_company_info(express_code)
        if company_info:
            company_code = company_info[0].get("comCode", "")
        else:
            return


        param = {}
        param['com'] = company_code or ''  # 快递公司编码
        param['num'] = express_code  # 快递单号
        param['phone'] = ''  # 手机号
        param['from'] = ''  # 出发地城市
        param['to'] = ''  # 目的地城市
        param['resultv2'] = '1'  # 开启行政区域解析
        pjson = json.dumps(param)  # 转json字符串

        postdata = {}
        postdata['customer'] = Express100.customer  # 查询公司编号
        postdata['param'] = pjson  # 参数数据

        # 签名加密
        str = pjson + Express100.key + Express100.customer
        md = hashlib.md5()
        md.update(str.encode())
        sign = md.hexdigest()
        postdata['sign'] = sign.upper()  # 加密签名

        # payload = {'type': company_code, 'postid': express_code, 'id': 1}
        # data = cls.get_json_data(cls.trace_url, payload)
        result = requests.post(cls.trace_url, postdata)

        return result


if __name__ == "__main__":
    while True:
        code = input("请输入快递单号：")
        res = Express100.get_express_info(str(code).strip())
        # print(json.dumps(res, ensure_ascii=False, sort_keys=True, indent=4))
        print(res.text)