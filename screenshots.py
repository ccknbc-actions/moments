import os
import re
import requests

links = []


def getLinkFriends(link):
    r"""获取bf友链页面的链接

    :param link: 你的友链地址
    """
    html = requests.get(url=link,verify=False).content
    links.extend(re.findall(re.compile(r'<a href="https://(.*?)"'), str(html)))


def downloadFriends(url_prefix="https://image.thum.io/get/width/1024/crop/768/wait/20/noanimate/https://",
                    url_suffix="", suffix="png"):
    r"""根据links里的友链下载到指定文件夹

    :param url_prefix: 截图网站前缀
    :param url_suffix: 截图网站后缀(如果有)
    :param suffix: 下载图片的后缀
    """
    # 去除 /
    for i in range(0, len(links)):
        links[i] = links[i].lstrip('//').rstrip('/')
    os.system("mkdir img")
    for link in links:
        os.system("curl " + url_prefix + link + url_suffix + " -o ./img/" + link.replace("/",".") + "." + suffix)


if __name__ == '__main__':
    getLinkFriends("https://ccknbc.vercel.app/blogroll/")
    downloadFriends()
