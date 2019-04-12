from django.conf.urls import url
from django.urls import reverse
from django import forms
from django.utils.safestring import mark_safe
from django.db.models.fields.related import ManyToManyField
from django.shortcuts import HttpResponse, render, redirect


class ModelStark(object):
    """
    默认配置类
    """
    list_display = ["__str__"]
    model_form_class = []
    def __init__(self, model):
        self.model = model
        # 方便调用
        self.model_name = self.model._meta.model_name
        self.app_label = self.model._meta.app_label

    # 反向解析当前查看表的增删改查的url
    def get_list_url(self):
        url_name = "%s_%s_list" % (self.app_label, self.model_name)
        _url = reverse(url_name)
        return _url

    def get_add_url(self):
        url_name = "%s_%s_add" % (self.app_label, self.model_name)
        _url = reverse(url_name)
        return _url

    def get_change_url(self, obj):
        url_name = "%s_%s_change" % (self.app_label, self.model_name)
        _url = reverse(url_name, args=(obj.pk,))
        return _url

    def get_delete_url(self, obj):
        url_name = "%s_%s_delete" % (self.app_label, self.model_name)
        _url = reverse(url_name, args=(obj.pk,))
        return _url

    # 默认操作函数
    def edit(self, obj=None, is_header=False):
        if is_header:
            return "操作"
        return mark_safe("<a href='%s'>编辑</a>" % self.get_change_url(obj))

    def delete(self, obj=None, is_header=False):
        if is_header:
            return "删除"
        return mark_safe("<a href='%s'>删除</a>" % self.get_delete_url(obj))

    def checkbox(self, obj=None, is_header=False):
        if is_header:
            return "选择"
        return mark_safe("<input type='checkbox' pk=%s>" % obj.pk)

    # 视图函数
    # 定义一个新的列表，既存放字段，有存放edit，delete，checkbox
    def new_list_display(self):
        temp = []
        # 把我原来的list_display数据添加进去
        temp.extend(self.list_display)
        # 把checkbox插入在第一位
        temp.insert(0, ModelStark.checkbox)
        # 继续往后添加edit字符串
        temp.append(ModelStark.edit)
        # 继续往后添加删除字符串
        temp.append(ModelStark.delete)
        return temp

    def listview(self, request):
        print(self)  # 当前访问模型表的配置类对象
        print(self.model)  # 当前访问模型表
        data_list = self.model.objects.all()
        print(self.list_display)
        # 构建表头
        # 想要的形式是这种形式header_list=["书籍名称","价格"]
        header_list = []
        for field_or_func in self.new_list_display():  # 依然循环["title","price","publish",edit]
            # 如果是函数的话这样
            if callable(field_or_func):
                # 如果是函数
                val = field_or_func(self, is_header=True)
            else:
                # # 如果只是单纯的字符串字段
                # 如果这个字段是__str__
                if field_or_func == "__str__":
                    val = self.model._meta.model_name.upper()
                    print(val)
                else:
                    # 获取到的是字段里边的verbose_name，如果没这个就是默认的表明
                    field_obj = self.model._meta.get_field(field_or_func)
                    val = field_obj.verbose_name
            header_list.append(val)

        # 构建数据表单部分
        new_data_list = []  # 先创建一个外层列表，在这个列表里边放小列表
        for obj in data_list:  # 循环 这个对应的列表，Queryset[book1,book2]
            temp = []  # 小列表
            for field_or_func in self.new_list_display():
                # 循环的就是你display中的东西，不仅有字段相对应的字符串，还可能有自定义的函数["title","price","publish",edit]
                # 故要做判断,callable是判断是否是函数，
                if callable(field_or_func):
                    # 如果是函数，则执行这个函数
                    val = field_or_func(self, obj)
                else:
                    # 如果是字符串，
                    # 如果是多对多字段，先导入一个from django.db.models.fields.related import ManyToManyField
                    # 这个是获取出来字段，
                    try:
                        field_obj = self.model._meta.get_field(field_or_func)
                        print(field_obj)
                        # app01.Book.title
                        # app01.Book.price
                        # app01.Book.publish
                        # app01.Book.authors
                        if isinstance(field_obj, ManyToManyField):
                            # 然后判断哪个字段是多对多字段，isinstance就是判断是否是多对多字段
                            # 如果是就要用.all()全部获取出来，
                            rel_data_list = getattr(obj, field_or_func).all()
                            print(rel_data_list)
                            # 获取出来每本书对应的作者这个对象
                            # <QuerySet [<Author: 沈巍>, <Author: 蓝忘机>]>
                            l = [str(item) for item in rel_data_list]
                            # 经过for循环，并且转成字符串，用|隔开
                            val = "|".join(l)
                        else:
                            # 如果不是多对多字段，就直接获取就行
                            val = getattr(obj, field_or_func)  # 反射
                    except Exception as e:
                        val = getattr(obj, field_or_func)  # 反射
                # 都添加到小列表中
                temp.append(val)
            # 添加到大列表中
            new_data_list.append(temp)
        # 在这个页面上增加一个增加数据的按钮，跳转到那个路径
        add_url = self.get_add_url()
        return render(request, "list_view.html", locals())

    # modelform
    def get_model_form(self):
        if self.model_form_class:
            # 如果不是使用的默认类,就是model_form_class不为空，有自己的配置类
            return self.model_form_class
        else:
            # 如果使用的是默认配置类的modelform
            class ModelFormClass(forms.ModelForm):
                class Meta:
                    # 就是关联的表名称
                    model = self.model
                    # 就是显示关联的字段名
                    fields = "__all__"

            return ModelFormClass

    # 编辑试图函数
    def addview(self, request):

        ModelFormClass = self.get_model_form()
        if request.method == "POST":
            # 获取数据
            form_obj = ModelFormClass(request.POST)
            # 校验数据
            if form_obj.is_valid():
                form_obj.save()  # 记得保存
                # 跳转到首页
                return redirect(self.get_list_url())
            # 这个返回是为了显示错误信息
            return render(request, "add_view.html", locals())
        # 实例化
        form_obj = ModelFormClass()
        return render(request, "add_view.html", locals())

    def changeview(self, request, id):
        ModelFormClass = self.get_model_form()
        # 选择要编辑的对象
        edit_obj = self.model.objects.get(pk=id)
        if request.method == "POST":
            form_obj = ModelFormClass(request.POST, instance=edit_obj)
            if form_obj.is_valid():
                form_obj.save()
                return redirect(self.get_list_url())
            return render(request,"change_view.html",locals())
        # 记得instance
        form_obj = ModelFormClass(instance=edit_obj)
        return render(request,"change_view.html",locals())

    def delview(self, request, id):
        if request.method == "POST":
            # 获取到所选择的对象
            self.model.objects.filter(pk=id).delete()
            return redirect(self.get_list_url())
        list_url = self.get_list_url()
        return render(request, "delete_view.html", locals())

    # 设计url，用反向解析，
    def get_urls(self):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        temp = [
            url(r"^$", self.listview, name="%s_%s_list" % (app_label, model_name)),
            url(r"add/$", self.addview, name="%s_%s_add" % (app_label, model_name)),
            url(r"(\d+)/change/$", self.changeview, name="%s_%s_change" % (app_label, model_name)),
            url(r"(\d+)/delete/$", self.delview, name="%s_%s_delete" % (app_label, model_name)),

        ]
        return temp

    @property
    def urls(self):
        return self.get_urls(), None, None


class AdminSite(object):
    """
        stark组件的全局类
    """

    def __init__(self):
        self._registry = {}

    def register(self, model, admin_class=None):
        # 设置配置类
        if not admin_class:
            admin_class = ModelStark
        self._registry[model] = admin_class(model)

    def get_urls(self):
        temp = []
        for model, config_obj in self._registry.items():
            model_name = model._meta.model_name
            app_label = model._meta.app_label
            temp.append(url(r"%s/%s/" % (app_label, model_name), config_obj.urls))
            # config_obj 获取的就是每个for循环中的BookConfig(Book)，publish，author遍历的对象
            '''
                      temp=[

                          #(1) url(r"app01/book/",BookConfig(Book).urls)
                          #(2) url(r"app01/book/",(BookConfig(Book).get_urls(), None, None))
                          #(3) url(r"app01/book/",([
                                                          url(r"^$", BookConfig(Book).listview),
                                                          url(r"add/$", BookConfig(Book).addview),
                                                          url(r"(\d+)/change/$", BookConfig(Book).changeview),
                                                          url(r"(\d+)/delete/$", BookConfig(Book).delview),
                                                   ], None, None))

                          ###########

                          # url(r"app01/publish/",([
                                                          url(r"^$", ModelStark(Publish).listview),
                                                          url(r"add/$",  ModelStark(Publish).addview),
                                                          url(r"(\d+)/change/$",  ModelStark(Publish).changeview),
                                                          url(r"(\d+)/delete/$",  ModelStark(Publish).delview),
                                                   ], None, None))
                      ]
                      '''

        return temp

    @property
    def urls(self):
        return self.get_urls(), None, None


site = AdminSite()
