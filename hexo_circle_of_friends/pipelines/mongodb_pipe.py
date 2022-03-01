# -*- coding:utf-8 -*-
# Author：yyyz
import os
import re
from datetime import datetime, timedelta
from pymongo import MongoClient
from .. import settings

today = (datetime.now() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')


class MongoDBPipeline:
    def __init__(self):
        self.userdata = []
        self.nonerror_data = set()  # 能够根据友链link获取到文章的人
        self.query_post_list = []

    def open_spider(self, spider):

        if settings.DEBUG:
            URI = "mongodb+srv://root:@cluster0.wgfbv.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
        else:
            URI = os.environ.get("MONGODB_URI")
        client = MongoClient(URI)
        db = client.fcircle
        self.posts = db.Post
        self.friends = db.Friend
        self.query_post_num = self.posts.count_documents({})

        for post in self.posts.find():
            self.query_post_list.append(post)

        self.friends.delete_many({})
        print("Initialization complete")

    def process_item(self, item, spider):
        if "userdata" in item.keys():
            li = []
            li.append(item["name"])
            li.append(item["link"])
            li.append(item["img"])
            self.userdata.append(li)
            # print(item)
            return item

        if "title" in item.keys():
            if item["author"] in self.nonerror_data:
                pass
            else:
                # 未失联的人
                self.nonerror_data.add(item["author"])

            # print(item)
            for query_item in self.query_post_list[:self.query_post_num]:
                try:
                    if query_item.get("link") == item["link"]:
                        query_item['created'] = min(item['created'], query_item.get("created"))
                        post_id = query_item.get("_id")
                        self.posts.delete_one({"_id": post_id})
                        return item
                except:
                    pass

            self.friendpoor_save(item)

        return item

    def close_spider(self, spider):
        # print(self.nonerror_data)
        # print(self.userdata)

        count, error_num = self.friendlist_push()
        self.outdate_clean(settings.OUTDATE_CLEAN)
        num = self.friendpoor_push()
        print("----------------------")
        print("友链总数 : %d" % count)
        print("失联友链数 : %d" % error_num)
        print("共 %d 篇文章" % num)
        print("最后运行于：%s" % today)
        print("done!")

    def outdate_clean(self, time_limit):
        out_date_post = 0
        for query_item in self.query_post_list:
            updated = query_item.get("updated")
            try:
                query_time = datetime.strptime(updated, "%Y-%m-%d")
                if (datetime.today() + timedelta(hours=8) - query_time).days > time_limit:
                    self.posts.delete_one({"_id": query_item.get("_id")})
                    query_item.clear()
                    out_date_post += 1
            except:
                self.posts.delete_one({"_id": query_item.get("_id")})
                query_item.clear()
                out_date_post += 1
        # print('\n')
        # print('共删除了%s篇文章' % out_date_post)
        # print('\n')
        # print('-------结束删除规则----------')

    def friendlist_push(self):
        friends = []
        error_num = 0
        for user in self.userdata:
            friend = {
                "name": user[0],
                "link": user[1],
                "avatar": user[2],
                "createdAt": today,
            }
            if user[0] in self.nonerror_data:
                # print("未失联的用户")
                friend["error"] = False
            elif settings.BLOCK_SITE:
                error = True
                for url in settings.BLOCK_SITE:
                    if re.match(url, friend["link"]):
                        friend["error"] = False
                        error = False
                if error:
                    print("请求失败，请检查链接： %s" % friend["link"])
                    friend["error"] = True
                    error_num += 1
            else:
                print("请求失败，请检查链接： %s" % friend["link"])
                friend["error"] = True
                error_num += 1
            friends.append(friend)
        if friends:
            self.friends.insert_many(friends)
        return len(friends), error_num

    def friendpoor_push(self):
        post_list = [item for item in self.query_post_list if item]
        self.posts.insert_many(post_list)
        return len(post_list)

    def friendpoor_save(self, item):
        item["createdAt"] = today
        self.query_post_list.append(item.copy())
        print("----------------------")
        print(item["author"])
        print("《{}》\n文章发布时间：{}\t\t采取的爬虫规则为：{}".format(item["title"], item["created"], item["rule"]))
