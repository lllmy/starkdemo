from stark.service.sites import site,ModelStark
from django.utils.safestring import mark_safe
from app01.models import Book, Publish, Author, AuthorDetail
from django.shortcuts import HttpResponse, render, redirect


class BookConfig(ModelStark):

    list_display = ["title", "price", "publish", "authors"]


site.register(Book, BookConfig)
site.register(Publish)
site.register(Author)