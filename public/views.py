#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from api.apiCommon import *
from common.common import *


# Create your views here.

@check_identify
def address_create(request):
    """
    新增收货地址
    :param request:
    :return:
    """
    data = request_body(request, "POST")
    if not data:
        return http_return(400, '请求错误')
    address = data.get("address", "")
    isDefault = data.get("isDefault", "")  # 1 不设置为默认地址， 2设置为默认地址
    contact = data.get("contact", "")
    tel = data.get("tel", "")
    area = data.get("area", "")
    if not address:
        return http_return(400, '请输入地址')
    selfUuid = data['_cache']['uuid']
    if not isDefault:
        return http_return(400, "请选择是否设为默认地址")
        if isDefault == 1:
            isDefault = False
        elif isDefault == 2:  # 设置为默认地址
            isDefault = True
            try:
                ReceivingInfo.objects.filter(userUuid__uuid=selfUuid).update(isDefault=False)
            except Exception as e:
                logging.error(str(e))
                return http_return(400, '设置默认地址失败')
    if not contact:
        return http_return(400, "请输入收件人姓名")
    if not tel:
        return http_return(400, "请输入收件人电话")
    if not tel_match(tel):
        return http_return(400, "手机号有误")
    if not areaUuid:
        return http_return(400, "请选择区域")
    if not area:
        return http_return(400, "未获取到地区信息")
    user = User.objects.filter(uuid=selfUuid).first()
    try:
        ReceivingInfo.objects.create(
            uuid=get_uuid(),
            userUuid=user,
            address=address,
            isDefault=isDefault,
            contact=contact,
            area=area,
            tel=tel,
        )
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '新增失败')
    return http_return(200, "新增成功")


@check_identify
def address_list(request):
    """
    收货地址列表
    :param request:
    :return:
    """
    data = request_body(request)
    if not data:
        return http_return(400, '请求错误')
    selfUuid = data['_cache']['uuid']
    receives = ReceivingInfo.objects.filter(userUuid__uuid=selfUuid).order_by("-updateTime").all()
    resList = []
    for rece in receives:
        resList.append({
            "uuid": rece.uuid,
            "area": rece.area if rece.area else "",
            "address": rece.address if rece.address else "",
            "isDefault": rece.isDefault,
            "contact": rece.contact if rece.contact else "",
            "tel": rece.tel if rece.tel else "",
        })
    return http_return(200, "成功", resList)


@check_identify
def address_change(request):
    """
    修改地址信息
    :param request:
    :return:
    """
    data = request_body(request, "POST")
    if not data:
        return http_return(400, '请求错误')
    uuid = data.get("uuid", "")
    area = data.get("area", "")
    isDefault = data.get("isDefault", "")
    contact = data.get("contact", "")
    tel = data.get("tel", "")
    updateData = {}
    selfUuid = data['_cache']['uuid']
    rece = ReceivingInfo.objects.filter(uuid=uuid)
    if not rece:
        return http_return(400, "未获取到地址信息")
    if area:
        updateData["area"] = area
    if isDefault:
        if isDefault == 2:
            updateData["isDefault"] = True
            try:
                ReceivingInfo.objects.filter(userUuid__uuid=selfUuid).update(isDefault=False)
            except Exception as e:
                logging.error(str(e))
                return http_return(400, '修改失败')
        else:
            updateData["isDefault"] = False
    if contact:
        updateData["contact"] = contact
    if tel:
        if not tel_match(tel):
            return http_return(400, "手机号有误")
        updateData["tel"] = tel
    try:
        updateData["updateTime"] = datetime.datetime.now()
        rece.update(**updateData)
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '修改失败')
    return http_return(200, "修改成功")


@check_identify
def address_del(request):
    """
    删除收货地址
    :param request:
    :return:
    """
    data = request_body(request, "POST")
    if not data:
        return http_return(400, '请求错误')
    uuid = data.get("uuid", "")
    rece = ReceivingInfo.objects.filter(uuid=uuid).first()
    if not rece:
        return http_return(400, "未获取到地址信息")
    rece.isDelete = True
    try:
        rece.save()
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '删除失败')
    return http_return(200, "删除成功")


@check_identify
def address_choose(request):
    """
    选择收货地址
    :param request:
    :return:
    """
    data = request_body(request, "POST")
    if not data:
        return http_return(400, '请求错误')
    receUuid = data.get("receUuid", "")
    if not receUuid:
        return http_return(400, "请选择收货地址")
    rece = ReceivingInfo.objects.filter(uuid=receUuid).first()
    if not rece:
        return http_return(400, "未获取到收货地址信息")

    userPrizeUuid = data.get("userPrizeUuid", "")
    if not userPrizeUuid:
        return http_return(400, "请选择收货奖品")
    userPrize = UserPrize.objects.filter(uuid=userPrizeUuid).first()
    if not userPrize:
        return http_return(400, "未获取到奖品信息")
    userPrize.receiveUuid = rece
    try:
        userPrize.save()
    except Exception as e:
        logging.error(str(e))
        return http_return(400, '选择收货地址失败')
    return http_return(200, "选择收货地址成功")


@check_identify
def area_create(request):
    """
    存储地区信息
    :param request:
    :return:
    """
    data = request_body(request, "POST")
    if not data:
        return http_return(400, '请求错误')
    url = "https://restapi.amap.com/v3/config/district"
    headers = {
        'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; InfoPath.3)'}
    params = {
        "key": "1d25cdd07a8b5fc88641e916afaf538e",
        "subdistrict": 3
    }
    res = requests.get(url, params=params, headers=headers)
    res.encoding = "utf-8"
    # html为json格式的字符串
    data = res.text
    # 把json格式字符串转为python数据类型
    data = json.loads(data)
    if data['info'] == "OK":
        try:
            info = data["districts"][0]
            with transaction.atomic():
                uuid1 = get_uuid()
                country = ChinaArea(
                    uuid=uuid1,
                    level=info['level'],
                    adcode=info['adcode'],
                    name=info['name'],
                    center=info['center'],
                )
                country.save()
                for pro in info['districts']:
                    uuid2 = get_uuid()
                    province = ChinaArea(
                        uuid=uuid2,
                        fatherUuid=country,
                        level=pro['level'],
                        adcode=pro['adcode'],
                        name=pro['name'],
                        center=pro['center'],
                    )
                    province.save()
                    for cit in pro['districts']:
                        uuid3 = get_uuid()
                        city = ChinaArea(
                            uuid=uuid3,
                            fatherUuid=province,
                            level=cit['level'],
                            adcode=cit['adcode'],
                            name=cit['name'],
                            center=cit['center'],
                        )
                        city.save()
                        for are in cit['districts']:
                            uuid4 = get_uuid()
                            area = ChinaArea(
                                uuid=uuid4,
                                fatherUuid=city,
                                level=are['level'],
                                adcode=are['adcode'],
                                name=are['name'],
                                center=are['center'],
                            )
                            area.save()
        except Exception as e:
            logging.error(str(e))
            print(str(e))
            return http_return(400, '失败')
    else:
        return http_return(400, '响应失败')
    return http_return(200, '成功')


def area_query(request):
    """
    区域信息获取
    :param request:
    :return:
    """
    uuid = request.GET.get('uuid', '')
    level = request.GET.get('level', '')
    name = request.GET.get('name', '')
    area = ChinaArea.objects
    if level:
        area = area.filter(level=level)
    if uuid:
        area = area.filter(fatherUuid__uuid=uuid)
    if name:
        area = area.filter(name__contains=name)
    areas = area.all()
    areaList = []
    for area in areas:
        areaList.append({
            "uuid": area.uuid,
            "name": area.name,
            "level": area.level,
        })
    return http_return(200, "成功", {"area": areaList})


def area_all(request):
    """
    区域信息获取
    :param request:
    :return:
    """
    area = ChinaArea.objects.filter(fatherUuid__isnull=True).first()
    provinces = area.children.all()
    provinceList = []
    for province in provinces:
        cityList = []
        cities = province.children.all()
        for city in cities:
            districtList = []
            districts = city.children.all()
            for district in districts:
                districtList.append({
                    "value": district.uuid,
                    "label": district.name,
                    "children": [],
                })
            cityList.append({
                "value": city.uuid,
                "label": city.name,
                "children": districtList,
            })
        provinceList.append({
            "value": province.uuid,
            "label": province.name,
            "children": cityList,
        })
    info = {
        "value": area.uuid,
        "label": area.name,
        "children": provinceList,
    }
    return http_return(200, "成功", info)
