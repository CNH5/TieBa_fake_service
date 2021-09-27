from django.db import models
from django.db.models import Model


# Create your models here.
# 重写BooleanField的to_python,居然能直接去改它的源码...


# 用户信息
class User(Model):
    class Gender(models.TextChoices):
        MALE = "男"
        FEMALE = "女"
        UNKNOWN = "未知"

    # 账号
    account = models.CharField(max_length=14, null=False, primary_key=True)
    # 密码
    password = models.CharField(null=False, max_length=20)
    # 注册时间
    registration_date = models.DateField(auto_now_add=True)
    # 昵称
    name = models.CharField(max_length=20)
    # 简介
    introduction = models.CharField(max_length=500, default="签名是一种态度，我想我可以更酷...")
    # 性别
    sex = models.CharField(max_length=2, choices=Gender.choices, default='未知')
    # 头像
    avatar = models.TextField(null=True)


# 储存吧名、吧头像、吧简介等
class Ba(Model):
    name = models.CharField(max_length=10, null=False)
    avatar = models.TextField(null=False)
    introduction = models.CharField(max_length=500, null=True)


# 帖子
class Tie(Model):
    # 帖子编号自带了
    # 帖子属于哪个吧
    ba = models.ForeignKey(Ba, default=1, on_delete=models.DO_NOTHING)
    # 帖子的发起账号
    poster = models.ForeignKey(User, on_delete=models.CASCADE)
    # 标题
    title = models.TextField(null=True)
    # 回复时间
    date = models.DateTimeField(auto_now_add=True)
    # 帖子信息
    info = models.TextField(null=True)
    # 图片
    img = models.TextField(null=True, default=None)
    # 楼层总数，
    floor_num = models.IntegerField(default=1)


# 楼层
class Floor(Model):
    # 回复的编号在django中默认有了，按从小到大排可以区分楼层数
    # 回复的账号
    poster = models.ForeignKey(User, on_delete=models.CASCADE)
    # 回复的帖子
    tie = models.ForeignKey(Tie, on_delete=models.CASCADE)
    # 用来统计帖子的总回复数
    reply_count = models.IntegerField(default=1)
    # 楼号
    floor = models.IntegerField(null=False)
    # 图片
    img = models.TextField(null=True, default=None)
    # 剩下的和上面差不多
    info = models.TextField(null=True)
    date = models.DateTimeField(auto_now_add=True)


# 层中层
class ReplyFloor(Model):
    poster = models.ForeignKey(User, on_delete=models.CASCADE)
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE)
    info = models.TextField(null=False)
    date = models.DateTimeField(auto_now_add=True)


# 下面全是用来找用户点赞记录的表
class TieLike(Model):
    # 应该把account和tie_id作为主码,
    poster = models.ForeignKey(User, on_delete=models.CASCADE)
    tie = models.ForeignKey(Tie, on_delete=models.CASCADE)
    type = models.BooleanField(null=False)

    class Meta:
        unique_together = ["poster", "tie"]


class FloorLike(Model):
    poster = models.ForeignKey(User, on_delete=models.CASCADE)
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE)
    type = models.BooleanField(null=False)

    class Meta:
        unique_together = ["poster", "floor"]


class ReplyFloorLike(Model):
    poster = models.ForeignKey(User, on_delete=models.CASCADE)
    reply_floor = models.ForeignKey(ReplyFloor, on_delete=models.CASCADE)
    type = models.BooleanField(null=False)

    class Meta:
        unique_together = ["poster", "reply_floor"]


# # 还有吧主小吧什么的表，不搞了


# # 经验表，吧和账号可以确定经验值
class Exp(Model):
    ba = models.ForeignKey(Ba, on_delete=models.DO_NOTHING)
    account = models.ForeignKey(User, on_delete=models.CASCADE)
    num = models.IntegerField(default=0)
    subscription = models.BooleanField(default=True)

    class Meta:
        unique_together = ["account", "ba"]


# 签到表
class SignIn(Model):
    ba = models.ForeignKey(Ba, on_delete=models.CASCADE)
    account = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ["account", "date", "ba"]


# 保存图片的表
class Images(Model):
    # 还能自动修改文件名，6
    img = models.ImageField(upload_to="images", null=False, blank=True)

# 修改模型：
# python manage.py makemigrations Model
# python manage.py migrate
