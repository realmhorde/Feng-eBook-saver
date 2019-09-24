
from requests_html import HTMLSession
from urllib import request,parse
#import urllib
import requests
import http.cookiejar
from bs4 import BeautifulSoup
import sys, getopt, time, os, re

opts, args = getopt.getopt(sys.argv[1:], "hi:o:")
input_file=""
output_file=""
for op, value in opts:
    if op == "-i":
        input_file = value
        #print(input_file)
    elif op == "-o":
        output_file = value
    elif op == "-h":
        quit

print('^^^^威锋电子书区资源挖掘脚本 v0.3^^^^')
print();
print('指定书名为 "'+input_file+'"，开始执行脚本')
print()

session = HTMLSession()
url="http://www.baidu.com/s?wd="+parse.quote(input_file)+'%20site%3Afeng.com'

def get_baidu_title_snap_from_url(url):
    mytitles = []
    headers={"Accept": "text/html, application/xhtml+xml, image/jxr, */*",

         "Accept - Encoding": "gzip, deflate, br",

         "Accept - Language": "zh - CN",

         "Connection": "Keep - Alive",
         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299",
         "referer":"baidu.com"}
    cjar = http.cookiejar.CookieJar()
    opener = request.build_opener(request.HTTPCookieProcessor(cjar))

    headall=[]
    for key,value in headers.items():
        item=(key,value)
        headall.append(item)
    opener.addheaders=headall
    request.install_opener(opener)
    data =request.urlopen(url).read().decode('utf-8')
    soup=BeautifulSoup(data,'html.parser')
    # 以格式化的形式打印html
    #print(soup.prettify());
    for result_table in soup.find_all('div',class_='result c-container'):
        title_table = result_table.find('h3');
        a_click = title_table.find("a");
        snap_url = result_table.find('a', class_='m')
        mytitles.append((a_click.get_text(), str(snap_url.get("href")))) # 标题
    return mytitles

def download_file(url, target_file_name):
    if os.path.exists(target_file_name):
        print("文件已存在，跳过");
        pass;

    retry_times = 0
    while retry_times < 5:
        try:
            resp = requests.get(url,
                                stream=True,
                                proxies=None,
                                timeout=30)
            #print(resp.status_code);
            if resp.status_code == 403:
                retry_times = 5
                print("Access Denied when retrieve %s.\n" % url)
                raise Exception("Access Denied")
            with open(target_file_name, 'wb') as fh:
                for chunk in resp.iter_content(chunk_size=1024):
                    fh.write(chunk)
            break
        except:
            # try again
            pass
        retry_times += 1
    else:
        try:
            os.remove(target_file_name)
        except OSError:
            pass
        print("Failed to retrieve %s from\n%s\n" % (target_file_name,
                                                    url))

def get_old_download_link(snapurl):
    urllist = [];
    linkcount = 1;
    try:
        baidusnap = session.get(snapurl)
    except:
        print('未知错误')
        return None

    results = baidusnap.html.find('a', containing=".epub");
    #print(results);
    for result in results:
        #linkattr = result.attrs
        #print(result);
        jqstart = result.html.find('jQuery.get')
        if jqstart != -1:
            #print(result)
            #print(jqstart)
            jqstart += 12
            jqend = result.html.find('.epub')
            if jqend == -1:
                print('附件 %n 不是epub格式电子书' % (linkcount));
                break;
            else:
                jqend += 5
                #print(result.html[jqstart:jqend])
                urllist.append(result.html[jqstart:jqend].replace('&amp;', '&'));
                #return result.html[jqstart:jqend].replace('&amp;', '&')
        else:
            print('===非可识别链接，跳过')
        linkcount += 1;

    if len(urllist) == 0:
        print('===未找到附件，尝试提取度盘链接')
        pancheck = -2
        for result in results:
            panstart = result.html.find("https://pan.baidu")
            if panstart != -1:
                link = result.attrs["href"];
                passcode = baidusnap.text.find(link) + len(link);
                #print(passcode);
                print("===", link, "提取码:", baidusnap.text[passcode+9:passcode+13]);
                pancheck = 0

        if pancheck == 0:return None;
        elif pancheck == -2:print("=== 未找到度盘链接");
    return urllist;

def validateTitle(title):
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, "_", title)  # 替换为下划线
    return new_title
    
def get_old_download_args(oldurl):
    #print(oldurl)
    try:
        trueurl = 'https://bbs.feng.com/' + oldurl
        #print(trueurl)
        weiphoneold = session.get(trueurl)
        results = weiphoneold.html.links
        result = list(results)[0];

        downargs = str(result).split("&");

        aid = "";
        filename = "";
        cnfilename = "";
        filedate = "";

        #print(downargs)
        for argstr in downargs:
            if argstr.find("aid=") != -1:
                aid = argstr[4:];
            elif argstr.find("name=") != -1:
                filename = argstr[5:].replace("+", "%20");
                cnfilename = validateTitle(parse.unquote(filename, encoding="UTF-8", errors='replace'));
                print("=== 附件名称:", cnfilename)
            elif argstr.find("url=") != -1:
                datestr = argstr[4:argstr.rfind("/")].replace("/","").replace("Day_","");
                if len(datestr) == 6 : datestr = "20" + datestr;
                dateobj = time.strptime(datestr, "%Y%m%d")
                filedate = time.strftime("%Y/%m/%d", dateobj)

        if aid != "" and filename != "" and filedate != "" :
            realfileurl = "https://bbs-att-qcloud.weiphone.net/"+filedate+"/"+aid+"_"+filename;
            cnfilefullname = os.path.join(os.getcwd(), "ebooks", cnfilename);
            #print(realfileurl);
            if os.path.exists(cnfilefullname):
                print("===", cnfilename, "文件已存在，跳过下载");
            else:
                download_file(realfileurl, cnfilefullname);
        else:
            print("===获取真实链接失败")
        return None
    except:
        print('未知错误')
        return None
    
baidulist = get_baidu_title_snap_from_url(url)

if baidulist is None or len(baidulist) == 0:
    print('未搜索到该电子书')
else:
    baidulen = len(baidulist)
    print('搜索结果总数',baidulen,'条（上限10条）')
    print()
    print('-尝试提取下载链接')
    print('|')
    count = 1
    for snapurl in baidulist:
        #print(snapurl)
        print("--结果",count)
        print('==='+snapurl[0],'===')
        oldurls = get_old_download_link(snapurl[1])
        
        if oldurls is not None:
            #print('3-尝试获取文件真实地址')
            #print(oldurl)
                #bookname = get_book_filename(oldurl)
                #print("=== 附件名称:", parse.unquote(bookname, encoding="UTF-8", errors='replace'))
                #print(oldurl);
            for attachurl in oldurls:
                get_old_download_args(attachurl);
        else:
            print('===未发现书籍地址')
        count += 1
        if count <= baidulen:
            print('|')
            time.sleep(3)
        

print()
print('脚本运行结束')
quit

    