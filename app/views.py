import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.db.models import BooleanField, F, Count, Q, Case, When, Max
from django.http import HttpResponse, JsonResponse

from Model.models import *


# 处理登录请求
def login(request):
    try:
        # 获取账号对应的密码
        ap = User.objects.get(pk=request.GET.get("account"))

    except ObjectDoesNotExist:
        # 查询结果为空，就是找不到账号
        return HttpResponse("账号不存在")

    else:
        if ap.password == request.GET.get("password"):
            # 账号和密码都正确，就是登录成功
            return HttpResponse("登陆成功")

        else:
            # 账号正确但是密码错误
            return HttpResponse("密码错误")


# 处理注册请求
def register(request):
    # 账号
    account = request.POST.get("account")
    # 密码
    password = request.POST.get("password")

    if unavailable(account) or unavailable(password):
        # 检验账号密码是否可用
        return HttpResponse("账号密码不能为空！")

    try:
        # 创建账号
        User.objects.create(
            account=account,
            password=password,
            name='tieba_' + account
        )

    except IntegrityError:  # 完整性错误，就是账号重复存在
        return HttpResponse("账号已存在")

    else:
        return HttpResponse("注册成功")


# request的变量不可用返回True
def unavailable(param):
    return param == "" or param is None


# 发帖
def append_tie(request):
    save_point = transaction.savepoint()

    img = request.FILES.get("img")
    title = request.POST.get("title")
    info = request.POST.get("info")

    if img is None and unavailable(title) and unavailable(info):
        return HttpResponse("请输入标题或图片")

    try:
        url = Images.objects.create(img=img).img.url if img is not None else None

        Tie.objects.create(
            poster_id=request.POST.get("account"),
            ba_id=request.POST.get("ba"),
            title=title,
            info=info,
            img=url,
        )
    except IntegrityError:
        transaction.rollback(save_point)
        return HttpResponse("invalid")

    except ValueError:
        transaction.rollback(save_point)
        return HttpResponse("data invalid!")

    else:
        return HttpResponse("succeed")


# 获取帖子的标题和点赞数
def get_tie_value(tie, account):
    return tie.extra(
        # 格式化时间,获取帖子的回复总数
        select={
            'date': 'DATE_FORMAT(model_tie.date, "%%Y-%%m-%%d %%H:%%i:%%s")',
            'reply_count': 'SELECT SUM(reply_count) FROM `model_floor` WHERE tie_id = `model_tie`.id'
        }
    ).values(
        "id", "date", "poster_id", "title", "info", "img",
        # 自定义的列也要选中
        "reply_count",
    ).annotate(
        ba_name=F("ba__name"),
        poster_name=F("poster__name"),
        poster_avatar=F("poster__avatar"),
        poster_exp=F("poster__exp__num"),
        good=Count("tielike", filter=Q(tielike__type=True), distinct=True),
        bad=Count("tielike", filter=Q(tielike__type=False), distinct=True),
        # 标记用户是否点赞过
        liked=Max(Case(
            When(
                tielike__poster_id=account,
                then=F("tielike__type"),
            ),
            output_field=BooleanField())
        )
        # 按照发帖时间排序,就是按照id降序
    )


# 获取帖子列表
def get_tie_list(request):
    result = get_tie_value(
        Tie.objects.filter(ba_id=request.GET.get("ba")),
        request.GET.get("account")
    ).order_by("-id")
    # print(result.query)  # 输出生成的sql语句,找bug

    return JsonResponse(list(result), safe=False)


def get_tie_by_id(request):
    result = get_tie_value(
        Tie.objects.filter(pk=request.GET.get("id")),
        request.GET.get("account")
    ).first()
    return JsonResponse(result, safe=False)


def get_tie_like(poster, tie):
    return TieLike.objects.get(poster=poster, tie=tie)


def get_floor_like(poster, floor):
    return FloorLike.objects.get(poster=poster, floor=floor)


def get_reply_like(poster, reply):
    return ReplyFloorLike.objects.get(poster=poster, reply_floor=reply)


def create_tie_like(poster, tie_id, like_type):
    TieLike.objects.create(poster_id=poster, tie_id=tie_id, type=like_type)


def create_floor_like(poster, floor, like_type):
    FloorLike.objects.create(poster_id=poster, floor_id=floor, type=like_type)


def create_reply_like(poster, reply_id, like_type):
    ReplyFloorLike.objects.create(poster_id=poster, reply_floor_id=reply_id, type=like_type)


get_like = {
    "tie": get_tie_like,
    "floor": get_floor_like,
    "reply": get_reply_like,
}

create_like = {
    "tie": create_tie_like,
    "floor": create_floor_like,
    "reply": create_reply_like,
}


# 点赞，有三种情况，
# 点赞，点踩，取消点赞或点踩,
# 点赞结果为空就取消点赞
def like(request):
    poster = request.POST.get("poster")
    like_type = request.POST.get("type")
    target_id = request.POST.get("id")
    target_type = request.POST.get("target_type")

    try:  # 先找有没有点赞记录，
        # get和filter不太一样
        record = get_like[target_type](poster, target_id)
    except ObjectDoesNotExist:  # 没找到,就新建一条
        try:
            create_like[target_type](poster, target_id, like_type)

        except IntegrityError or ValueError:
            return HttpResponse("invalid")

        else:
            return HttpResponse("add succeed")
    else:
        # 之前没有报错，说明已经存在点赞记录,就应当更新点赞类型或取消点赞
        if like_type != "":
            record.type = like_type
            record.save()
            return HttpResponse("update succeed")

        else:
            record.delete()
            return HttpResponse("cancel succeed")


def get_floor_list(floor, account, order):
    return floor.extra(
        select={'date': 'DATE_FORMAT(model_floor.date, "%%Y-%%m-%%d %%H:%%i:%%s")'}
    ).values(
        "id", "poster_id", "date", "floor", "info", "img",
    ).annotate(
        poster_name=F("poster__name"),
        poster_avatar=F("poster__avatar"),
        poster_exp=F("poster__exp__num"),
        reply_count=F("reply_count") - 1,
        good=Count("floorlike", filter=Q(floorlike__type=True), distinct=True),
        bad=Count("floorlike", filter=Q(floorlike__type=False), distinct=True),
        liked=Max(Case(
            When(
                floorlike__poster=account,
                then=F("floorlike__type")),
            output_field=BooleanField())
        )
    ).order_by(order)


# 根据传入的帖子id获取楼层详细数据,还要搞排序...
def get_floor(request):
    floor = Floor.objects.filter(tie_id=request.GET.get("tie"))

    if request.GET.get("condition") == "only_tie_poster":  # 这里还可以有其它限制..
        floor = floor.filter(poster_id=F("tie__poster"))

    result = get_floor_list(
        floor=floor,
        account=request.GET.get("account"),
        order=request.GET.get("order")
    )

    return JsonResponse(list(result), safe=False)


# 获取楼层的回复,
def get_reply_floor(request):
    result = ReplyFloor.objects.filter(floor_id=request.GET.get("floor")).extra(
        select={'date': 'DATE_FORMAT(date, "%%Y-%%m-%%d %%H:%%i:%%s")'}
    ).values(
        "id", "poster_id", "info", "date",
    ).annotate(
        poster_name=F("poster__name"),
        poster_avatar=F("poster__avatar"),
        poster_exp=F("poster__exp__num"),
        good=Count("replyfloorlike", filter=Q(replyfloorlike__type=True), distinct=True),
        bad=Count("replyfloorlike", filter=Q(replyfloorlike__type=False), distinct=True),
        liked=Max(Case(
            When(
                replyfloorlike__poster=request.GET.get("account"),
                then=F("replyfloorlike__type")),
            output_field=BooleanField())
        )
    ).distinct().order_by("id")

    return JsonResponse(list(result), safe=False)


# 添加楼层，就是回复帖子
@transaction.atomic
def append_floor(request):
    save_point = transaction.savepoint()

    tie_id = request.POST.get("tie")
    info = request.POST.get("info")
    img = request.FILES.get("img")

    if img is None and unavailable(info):
        return HttpResponse("回帖内容不能为空!")

    try:
        tie = Tie.objects.filter(pk=tie_id).first()
        tie.floor_num = tie.floor_num + 1
        tie.save()

        Exp.objects.filter(
            account_id=request.POST.get("account"),
            ba_id=tie.ba_id,
        ).update(num=F('num') + 3)

        url = Images.objects.create(img=img).img.url if img is not None else None

        # 新增楼层
        Floor.objects.create(
            poster_id=request.POST.get("account"),
            tie_id=tie_id,
            info=info,
            floor=tie.floor_num,
            img=url
        )

    except IntegrityError:
        transaction.rollback(save_point)
        return HttpResponse("invalid")

    else:
        return HttpResponse("succeed")


# 回复楼层
@transaction.atomic
def append_reply_floor(request):
    save_point = transaction.savepoint()

    poster = request.POST.get("account")
    floor = request.POST.get("floor")
    info = request.POST.get("info")

    try:
        f = Floor.objects.filter(pk=floor)
        f.update(reply_count=F("reply_count") + 1)

        Exp.objects.filter(
            account_id=poster,
            ba_id=f.annotate(ba=F("tie__ba")).first().ba,
        ).update(num=F('num') + 3)

        ReplyFloor.objects.create(
            poster_id=poster,
            floor_id=floor,
            info=info,
        )

    except IntegrityError:
        transaction.rollback(save_point)
        return HttpResponse("invalid")

    else:
        return HttpResponse("succeed")


# 保存图片,不过好像保存文件也行？
def save_image(request):
    """
    :param request:
    :return: 返回应当是图片的编号
    """
    img_obj = request.FILES.get("img")
    return HttpResponse(Images.objects.create(img=img_obj).img.url) \
        if img_obj is not None else HttpResponse("没有发送图片")


# 获取用户信息
def get_user_info(request):
    try:
        user = User.objects.filter(pk=request.GET.get('target')).extra(
            select={'registration_date': 'DATE_FORMAT(registration_date, "%%Y-%%m-%%d")'}
        ).values(
            "account",
            "registration_date",
            "name",
            "introduction",
            "sex",
            "avatar"
        ).first()

    except ObjectDoesNotExist:
        return HttpResponse("invalid")

    else:
        return JsonResponse(user, safe=False)


# 获取用户发过的帖子
def get_user_tie(request):
    target_id = request.GET.get("target")
    account = request.GET.get("account")
    result = Tie.objects.filter(poster_id=target_id).extra(
        # 格式化时间,获取帖子的回复总数
        select={
            'date': 'DATE_FORMAT(model_tie.date, "%%Y-%%m-%%d %%H:%%i:%%s")',
            'reply_count': 'SELECT SUM(reply_count) FROM `model_floor` WHERE tie_id = `model_tie`.id',
        }
    ).values(
        "id",
        "date",
        "poster_id",
        "title",
        "info",
        "img",
        # 自定义的列也要选中
        "reply_count",
    ).annotate(
        ba_name=F("ba__name"),
        poster_name=F("poster__name"),
        poster_avatar=F("poster__avatar"),
        poster_exp=F("poster__exp__num"),
        good=Count("tielike", filter=Q(tielike__type=True), distinct=True),
        bad=Count("tielike", filter=Q(tielike__type=False), distinct=True),
        # 标记用户是否点赞过
        liked=Max(Case(
            When(
                tielike__poster_id=account,
                then=F("tielike__type"),
            ),
            output_field=BooleanField())
        )
        # 按照发帖时间排序,就是按照id降序
    ).order_by("-id")

    return JsonResponse(list(result), safe=False)


# 获取吧信息
def get_ba(request):
    account_id = request.GET.get("account")

    try:
        ba = Ba.objects.filter(pk=request.GET.get("ba")).first()

        exp = Exp.objects.filter(account_id=account_id, ba=ba).first()

        is_sign = SignIn.objects.filter(
            account_id=account_id, ba=ba,
            date=datetime.datetime.now()
        ).exists()
    except ValueError as e:
        return HttpResponse(e.__str__())

    else:
        result = ba.__dict__
        result.pop("_state")
        result["exp"] = 0 if exp is None else exp.num
        result["subscription"] = False if exp is None else exp.subscription
        result["signed"] = is_sign

        return JsonResponse(result, safe=False)


@transaction.atomic()
def sign(request):
    save_point = transaction.savepoint()

    try:
        sign_id = SignIn.objects.create(
            ba_id=request.POST.get("ba"),
            account_id=request.POST.get("account"),
        ).pk

        Exp.objects.filter(
            ba_id=request.POST.get("ba"),
            account_id=request.POST.get("account"),
        ).update(num=F("num") + 8)

        no = SignIn.objects.filter(
            id__lte=sign_id,
            date=datetime.date.today()
        ).annotate(num=Count("id")).first()

    except IntegrityError or ValueError:
        transaction.rollback(save_point)
        return HttpResponse("invalid")

    else:
        return HttpResponse(no.num)


# 修改用户信息
def change_user_info(request):
    introduction = request.POST.get('introduction')
    try:
        n = User.objects.filter(pk=request.POST.get('account')).update(
            name=request.POST.get('name'),
            sex=request.POST.get('sex'),
            introduction="签名是一种态度，我想我可以更酷..." if introduction is None else introduction,
        )
    except ValueError as e:
        return HttpResponse(e.__str__())

    else:
        return HttpResponse('user invalid' if n == 0 else "succeed")


# 修改头像
@transaction.atomic
def change_avatar(request):
    save_point = transaction.savepoint()
    try:
        avatar = Images.objects.create(img=request.FILES.get("avatar")).img.url

        User.objects.filter(pk=request.POST.get("account")).update(avatar=avatar)

    except ValueError:
        transaction.rollback(save_point)
        return HttpResponse("file invalid")

    except ObjectDoesNotExist:
        transaction.rollback(save_point)
        return HttpResponse("account don't exists")

    else:
        return HttpResponse("succeed")


# 关注某个吧
def subscription_ba(request):
    ba = str(request.POST.get("ba"))
    account = str(request.POST.get("account"))
    try:
        Exp.objects.create(ba_id=ba, account_id=account)
    except IntegrityError:
        Exp.objects.filter(
            ba_id=ba,
            account_id=account,
        ).update(subscription=True)

        return HttpResponse("关注成功!")

    except ValueError:
        return HttpResponse("数据异常!")

    else:
        return HttpResponse("关注成功!")


def normal(request):
    return HttpResponse("后端正常运行！")
