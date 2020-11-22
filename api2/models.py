from re import T
from django.db import models

# Create your models here.
class Category(models.Model):
    category_id = models.CharField(max_length=100,primary_key=True)
    name = models.CharField(max_length=100)
    super_category = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, db_column="super_category")

class Good(models.Model):
    good_id = models.AutoField(primary_key=True)
    name = models.TextField(null=True)
    price = models.DecimalField(null=True, decimal_places=2, max_digits=20)
    description = models.TextField(null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, db_column="category")
    rating = models.IntegerField()
    image = models.TextField()

class Good_Label(models.Model):
    good = models.ForeignKey(Good, on_delete=models.SET_NULL, null=True, db_column="good")
    label = models.CharField(max_length=100)

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    token = models.TextField()
    password = models.CharField(max_length=300,null=True)
    user_name = models.CharField(max_length=100,null=True)

class Suggestion(models.Model):
    suggestion_id = models.AutoField(primary_key=True)
    from_good = models.ForeignKey(Good, on_delete=models.SET_NULL, null=True, db_column="from")

for i in range(0,51):
    Suggestion.add_to_class("to_"+str(i), models.ForeignKey(Good, on_delete=models.SET_NULL, null=True, related_name="to"+str(i)))


class Cart_Item(models.Model):
    cart_item_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_column="user")
    good = models.ForeignKey(Good, on_delete=models.SET_NULL, null=True, db_column="good")
    timestamp = models.DateTimeField(auto_now=True)
    removed = models.BooleanField(default=False)

class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    order_group = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_column="order_group")
    good = models.ForeignKey(Good, on_delete=models.SET_NULL, null=True, db_column="good")
    extra = models.TextField(null=True)

class Order_Group(models.Model):
    order_group_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_column="user")
    create_time = models.DateTimeField(auto_now=True)
    pruchased = models.BooleanField(default=False)
    purchased_time = models.DateTimeField(null=True)
    canceled = models.BooleanField(default=False)
    canceled_time = models.DateTimeField(null=True)
    finished = models.BooleanField(default=False)
    finished_time = models.DateTimeField(null=True)
    extra = models.TextField(null=True)
    cost = models.DecimalField(null=True, decimal_places=2, max_digits=20)