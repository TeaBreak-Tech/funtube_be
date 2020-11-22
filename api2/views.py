from re import U
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed
from django.views.decorators.http import require_http_methods
from secrets import token_urlsafe

from .models import *

import json
import uuid
import re
import random

TOKEN_LENGTH = 50
G_DNE = HttpResponse(content="Good Not Found", status=404, reason="G-DNE")
U_DNE = HttpResponse(content="User Not Found", status=404, reason="U-DNE")
C_DNE = HttpResponse(content="Category Not Found", status=404, reason="C-DNE")
N_AUTH = HttpResponse(content="Not Authorized", status=403, reason="N-AUTH")
B_PAR = HttpResponse(content="Blank or missing required parameter", status=400, reason="B-PAR")

# Create your views here.
def good(request):
    if request.method == 'GET':
        def toDict(good):
            if good.category:
                category = {
                    "name": good.category.name,
                    "category_id": good.category.category_id,
                }
            else:
                category = None
            return {
                "good_id":good.good_id,
                "name":good.name,
                "price":good.price,
                "rating":good.rating,
                "category":category,
                "description":good.description,
                "image":good.image,
            }
        mode = request.GET.get("mode", "single") # mode: single/list_all/filter
        label = request.GET.get("label", None)
        category_id = request.GET.get("cid", None)
        if category_id:
            try:
                category = Category.objects.get(pk=category_id)
                category_name = category.name
            except: return C_DNE
        else: category = None; category_name = None
        if mode=="single":
            good_id = request.GET.get("gid", None)
            try: good = Good.objects.get(pk=good_id)
            except: return G_DNE
            return JsonResponse( toDict(good) )
        elif mode=="list_all":
            goods = Good.objects.all()
            good_list = [ toDict(good) for good in goods]
            return JsonResponse( {"result":good_list} )
        elif mode=="list":
            if label:
                good_list = [ good_label.good for good_label in Good_Label.objects.filter(label=label) ]
            elif category:
                goods = Good.objects.filter(category=category)
                good_list = [ toDict(good) for good in goods]
            else:
                goods = Good.objects.all()
                good_list = [ toDict(good) for good in goods]
            return JsonResponse( {"category_name":category_name,"result":good_list} )

    elif request.method == 'POST':
        body_dict = json.loads(request.body.decode('utf-8'))
        name = body_dict.get("name")
        price = body_dict.get("price",0)
        rating = int(body_dict.get("rating",3))
        description = body_dict.get("description")
        category_id = body_dict.get("category_id",None)
        image = body_dict.get("image")
        if category_id:
            try: category = Category.objects.get(pk=category_id)
            except: return C_DNE
        else: category = None
        good = Good()
        good.name = name
        good.price = price
        good.rating = rating
        good.category = category
        good.description = description
        good.image = image
        good.save()
        return JsonResponse({"result":"success", "id":good.good_id })
    
    elif request.method == 'PATCH':
        body_dict = json.loads(request.body.decode('utf-8'))
        good_id = request.GET.get("gid", None)
        try: good = Good.objects.get(pk=good_id)
        except: return G_DNE
        name = body_dict.get("name",good.name)
        price = body_dict.get("price",good.price)
        rating = int(body_dict.get("rating",good.rating))
        description = body_dict.get("description",good.description)
        category_id = body_dict.get("category_id",None)
        image = body_dict.get("image",good.image)
        if category_id:
            try: category = Category.objects.get(pk=category_id)
            except: return C_DNE
        else:
            category = good.category
        good.name = name
        good.price = price
        good.rating = rating
        good.category = category
        good.description = description
        good.image = image
        good.save()
        return JsonResponse({
            "result":"success",
            "good_id":good.good_id,
            "name":good.name,
            "price":good.price,
            "rating":good.rating,
            "category":good.category.name,
            "description":good.description,
            "image":good.image,
        })
    
    else:
        return HttpResponseNotAllowed(["POST","GET","PATCH","DELETE"])

def generateSuggestions(request):
    if request.method == 'GET':
        for good in  Good.objects.all():
            rand_ids = random.sample(range(1, Suggestion.objects.all().count()), min(Suggestion.objects.all().count(),50))
            suggest_goods = Good.objects.filter(suggestion_id__in=rand_ids)
            for i in range(1,51):
                setattr( good, "to_"+str(i), suggest_goods[i] )
            good.save()
        return JsonResponse({"status":"success",})
    else:
        return HttpResponseNotAllowed(["POST","GET","PATCH","DELETE"])

def suggestion(request):
    if request.method == 'GET':
        good_id = request.GET.get("gid", None)
        try: good = Good.objects.get(pk=good_id)
        except: return G_DNE
        suggestion = Suggestion.objects.get(good=good)
        suggestions = suggestion.__dict__.values[2:]
        return JsonResponse({"result":[good.__dict__ for good in suggestions]})
    else:
        return HttpResponseNotAllowed(["POST","GET","PATCH","DELETE"])

def category(request):
    if request.method == 'GET':
        scid = request.GET.get("scid", None)
        list_all = bool(request.GET.get("list_all", False))
        if list_all:
            categories = Category.objects.all()
        else:
            if scid:
                try: super_category = Category.objects.get(pk=scid)
                except: return C_DNE
            else: super_category = None
            categories = Category.objects.all().filter(super_category=super_category)
        category_list = [{
            "category_id":category.category_id,
            "name":category.name,
        } for category in categories]
        return JsonResponse( {"result":category_list} )
    elif request.method == 'POST':
        body_dict = json.loads(request.body.decode('utf-8'))
        category_id = body_dict.get("category_id")
        if not category_id:
            return B_PAR
        name = body_dict.get("name",category_id)
        super_category_id = body_dict.get("super_category_id")
        if super_category_id:
            try:super_category = Category.objects.get(pk=super_category_id)
            except: return C_DNE
        else:super_category = None
        category = Category()
        category.category_id = category_id
        category.name = name
        category.super_category = super_category
        category.save()
        return JsonResponse({"status":"success","category_id":category_id},status=201)



def good_label(request):
    if request.method == 'GET':
        good_labels = list(Good_Label.objects.values("label")) 
        return JsonResponse({"result":good_labels})

def user(request):
    print("Login?")
    if request.method == 'POST':
        new = request.GET.get("new", "false")
        token = request.COOKIES.get("token")
        user_id = request.COOKIES.get("user_id")

        body_dict = json.loads(request.body.decode('utf-8'))
        identity = body_dict.get("identity")
        password = body_dict.get("password")

        if not identity:
            # 不提供identity的用于已登录用户确认登录状态
            try:
                user = User.objects.get(pk=user_id)
                tokens = user.token.split(' ')
                if token in tokens:
                    #如果token可用，继续使用
                    response = JsonResponse({
                        "user_id":user.user_id,
                        "user_name":user.user_name,
                    })
                    response.set_cookie("user_id",user.user_id,secure=True)
                    response.set_cookie("user_name",user.user_name)
                    response.set_cookie("token",token,secure=True)
                    return response
                elif password==user.password:
                    # 如果token已经不可用，但是提供了有效的密码，则新增一个token来使用
                    token = token_urlsafe(TOKEN_LENGTH)
                    response = JsonResponse({
                        "user_id":user.user_id,
                        "user_name":user.user_name,
                    })
                    user.token = ' '.join(user.topen.split(' ').append(token))
                    user.save()
                    response.set_cookie("user_id",user.user_id,secure=True)
                    response.set_cookie("user_name",user.user_name)
                    response.set_cookie("token",token,secure=True)
                    return response
                else:
                    #如果也没提供有效密码，则视为强制下线，交由前端处理
                    response = JsonResponse({
                        "user_id":None,
                        "user_name":None,
                    },status=405)
                    response.set_cookie("user_name",user.user_name)
                    response.set_cookie("is_login","false")
                    return response
            except:
                # 为RA研究专门准备的接口，在不提供identity而且用户不存在的时候自动创建用户
                user = User()
                user.user_name = "Research-User"
                user.password = "Research-Password"
                user.token = token_urlsafe(TOKEN_LENGTH)
                user.save()
                response = HttpResponse({"user_id":user.user_id},status=201)
                response.set_cookie("user_id",user.user_id,secure=True)
                response.set_cookie("user_name",user.user_name)
                response.set_cookie("token",token,secure=True)
                return response
        # 提供了identity的话，忽视以上逻辑
        else:
            # 未登陆状态，使用用户名或id + 密码 进行登录
            try: user = User.objects.get(pk=identity)
            except:
                try: user = User.objects.get(user_name=identity)
                except:
                    # 或者可以创建新用户
                    if new=="true":
                        user = User()
                        user.user_name = identity
                        user.password = password
                        user.token = token_urlsafe(TOKEN_LENGTH)
                        user.save()
                        response = HttpResponse({"user_id":user.user_id},status=201)
                        response.set_cookie("user_id",user.user_id,secure=True)
                        response.set_cookie("user_name",user.user_name)
                        response.set_cookie("token",token,secure=True)
                    else: return U_DNE
            if password==user.password:
                # 成功登录
                if token not in user.token.split(' '):
                    token = token_urlsafe(TOKEN_LENGTH)
                    user.token = ' '.join(user.topen.split(' ').append(token))
                    user.save()
                response = JsonResponse({
                    "user_id":user.user_id,
                    "user_name":user.user_name,
                })
                response.set_cookie("user_id",user.user_id,secure=True)
                response.set_cookie("user_name",user.user_name)
                response.set_cookie("token",token,secure=True)
            else:
                # 密码错误
                response = JsonResponse({
                    "user_id":None,
                    "user_name":None,
                },status=405)
                #response.set_cookie("user_id",user.user_id,secure=True)
                #response.set_cookie("user_name",user.user_name)
                #response.set_cookie("token",token,secure=True)
            return response
    elif request.method == 'GET':
        uid = request.GET.get("uid", False)
        if uid:
            try: user = User.object.get(pk=uid)
            except: return U_DNE
            return JsonResponse({
                "user_name":user.user_name
            })
        else:
            result = [{
                "user_name":user.user_name,
            } for user in User.objects.all()]
            return JsonResponse(result)
    else:
        return HttpResponseNotAllowed(["POST","GET","PATCH","DELETE"])



def cart(request):
    token = request.COOKIES.get("token")
    user_id = request.COOKIES.get("user_id")
    try: user = User.objects.get(pk=user_id)
    except: return U_DNE
    if token not in user.token.split(' '):
        return N_AUTH

    if request.method == 'POST':
        body_dict = json.loads(request.body.decode('utf-8'))
        good_id = body_dict.get("good_id")
        try: good = Good.objects.get(pk=good_id)
        except: return G_DNE
        cart_item = Cart_Item()
        cart_item.user = user
        cart_item.good = good
        cart_item.save()
        return JsonResponse({})
    elif request.method == 'GET':
        raw_cart_items = [{
            "good_id": cart_item.good.good_id
        } for cart_item in Cart_Item.objects.filter(user=user).filter(removed=False)]
        cart_items = []
        for raw_cart_item in raw_cart_items:
            for cart_item in cart_items:
                if cart_item["good_id"]==raw_cart_item["good_id"]:
                    cart_item["count"]+= 1
                    break
            else:
                cart_items.append({
                    "good_id":raw_cart_item["good_id"],
                    "count":1,
                })
        return JsonResponse(cart_items)
    elif request.method == 'DELETE':
        token = request.COOKIES.get("token")
        user_id = request.COOKIES.get("user_id")
        try: user = User.objects.get(pk=user_id)
        except: return U_DNE
        if token not in user.token.split(' '):
            return N_AUTH

        good_id = request.GET.get("gid", "")
        try: good = Good.objects.get(pk=good_id)
        except: return G_DNE
        cart_items = Cart_Item.objects.filter(user=user).filter(removed=False).filter(good=good).order_by("timestamp")
        if cart_items.count() >= 1:
            cart_item = cart_items[0]
            cart_item.removed = False
            cart_item.save()
        else:
            return HttpResponse("No more item to remove from cart",status=500)

def order(request):
    token = request.COOKIES.get("token")
    user_id = request.COOKIES.get("user_id")
    try: user = User.objects.get(pk=user_id)
    except: return U_DNE
    if token not in user.token.split(' '):
        return N_AUTH
    
    if request.method == 'GET':
        orders = [{
            "order_group_id": order_group.order_group_id,
            "create_time": order_group.create_time,
            "purchased": order_group.purchased,
            "canceled": order_group.canceled,
            "finished": order_group.finished,
            "extra": order_group.extra,
            "cost": order_group.cost,
            "goods": [{
                "order_id":order.order_id,
                "good_id":order.good.good_id,
                "name":order.good.name,
                "price":order.good.price,
                "extra": order.extra,
            } for order in Order.objects.filter(order_group=order_group)]
        } for order_group in Order_Group.objects.filter(user=user)]
        return JsonResponse(orders)

    elif request.method == 'POST':
        body_dict = json.loads(request.body.decode('utf-8'))
        order_group = Order_Group()
        order_group.user = user
        order_group.extra = body_dict.get("extra","")
        cost = 0
        for item in body_dict.get("items",[]):
            cart_item_id = item.get("cart_item_id")
            good_id = item.get("good_id")
            try:
                cart_item = Cart_Item.objects.filter(user=user).filter(removed=False).get(pk=cart_item_id)
                cart_item.removed = True
                cart_item.save()
                good = cart_item.good
            except:
                cart_item = None
                try: good = Good.objects.get(pk=good_id)
                except: return G_DNE
            cost += good.price
            order = Order()
            order.order_group = order_group
            order.good = good
            order.extra = item.get("extra","")
            order.save()
        order_group.save()


    
    