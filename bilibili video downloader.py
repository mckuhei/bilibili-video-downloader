import os,time,requests,json,qrcode,sys,argparse,threading,traceback,re
import tkinter as tk
from io import BytesIO
from PIL import ImageTk
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, wait
table='fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF'
tr={}
for i in range(58):
    tr[table[i]]=i
s=[11,10,3,8,4,6]
xor=177451812
add=8728348608

def dec(x):
    r=0
    for i in range(6):
        r+=tr[x[s[i]]]*58**i
    return (r-add)^xor
################################
cookie={}

def login():
    w=tk.Tk()
    w.geometry("390x390")
    w.resizable(False, False)
    w.title("扫码登录bilibili")
    canvas=tk.Canvas(w,width=390,height=390)
    canvas.pack()
    while 1:
        qrcode1=requests.get("http://passport.bilibili.com/qrcode/getLoginUrl").json()
        url=qrcode1["data"]["url"]
        oauthKey=qrcode1["data"]["oauthKey"]
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=1
        )
        qr.add_data(url)
        qr.make(fit=True)
        img=ImageTk.PhotoImage(image=qr.make_image().resize((390,390)))
        canvas.create_image(390/2,390/2,image=img)
        while 1:
            for i in range(20):
                w.update()
                time.sleep(0.1)
            qrcode2=requests.post("http://passport.bilibili.com/qrcode/getLoginInfo",data={"oauthKey":oauthKey})
            #print(qrcode2.text)
            if qrcode2.json()["data"]==-2 or qrcode2.json()["data"]==-1:
                #print("更新oauthKey")
                break
            if type(qrcode2.json()["data"])==dict:
                w.destroy()
                return requests.utils.dict_from_cookiejar(qrcode2.cookies)
################################

suffixes = {1000: ['KB','MB','GB','TB','PB','EB','ZB','YB'],
            1024: ['KiB','MiB','GiB','TiB','PiB','EiB','ZiB','YiB']}

def approximate_size(size,a_kilobyte_is_1024_bytes=False):
    if size < 0:
        raise ValueError('number must be non-negative')
    multiple = 1024 if a_kilobyte_is_1024_bytes else 1000
    for suffix in suffixes[multiple]:
        size /= multiple
        if size < multiple:
            return '{0:.2f}{1}'.format(size,suffix) #'{0:.2f} {1}'之间的空格可以省略
#https://blog.csdn.net/wudinaniya/article/details/105898075
cookie=None

length,now,value=0,0,0

status_URL="http://api.bilibili.com/x/web-interface/view?aid=%s"
stream_URL="http://api.bilibili.com/x/player/playurl?avid=%s&cid=%s"
#{'referer':'https://www.bilibili.com/video/av621176'}
def download(file,URL,cookies=None,headers=None):
    content=requests.get(URL,cookies=None,headers=headers,stream=True)
    if content.status_code!=200 and content.status_code!=206: exit(content.status_code)
    length=int(content.headers["Content-Length"])
    now=0
    startTime=time.perf_counter()
    for chunk in content.iter_content(1024):
            file.write(chunk)
            now+=len(chunk)
            value=int((now/length)*100)
            sys.stdout.write("\r%s |%s%s| %s/s \b"%(str(value)+"%","█"*int(value/2),"  "*(50-int(value/2)),approximate_size(now/(time.perf_counter()-startTime))))
            sys.stdout.flush()


lock = Lock()

class Downloader():
    def __init__(self, url, nums, file,size=None):
        self.url = url
        self.num = nums
        self.name = file
        headers = {}
        headers["Referer"]='https://www.bilibili.com/'
        headers["Origin"]="https://www.bilibili.com"
        headers["User-Agent"]="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
        r = requests.get(self.url,headers=headers,stream=True)
        # 若资源显示302,则迭代找寻源文件
        while r.status_code == 302:
            self.url = r.headers['Location']
            print("该url已重定向至{}".format(self.url))
            r = get(self.url,headers=headers,stream=True)
        self.size = size if size else int(r.headers['Content-Length'])
        print('该文件大小为：{} bytes'.format(self.size))
        self.length=0
        self.start=time.perf_counter()

    def down(self, start, end, fp):
        headers = {'Range': 'bytes={}-{}'.format(start, end)}
        headers["Referer"]='https://www.bilibili.com/video/av%s'%(avid,)
        headers["Origin"]="https://www.bilibili.com"
        headers["User-Agent"]="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
        # stream = True 下载的数据不会保存在内存中
        r = requests.get(self.url, headers=headers, stream=True)
        offset=start
        for i in r.iter_content(1024):
            lock.acquire()
            fp.seek(offset)
            self.length=self.length+len(i)
            offset+=len(i)
            fp.write(i)
            lock.release()

    def showPercent(self):
        while 1:
            value=int((self.length/self.size)*100)
            sys.stdout.write("\r%s |%s%s| %s/s \b"%(str(value)+"%","█"*int(value/2),"  "*(50-int(value/2)),approximate_size(self.length/(time.perf_counter()-self.start))))
            sys.stdout.flush()
            if self.size<=self.length: break
            #time.sleep(0.05)


    def run(self):
        # 创建一个和要下载文件一样大小的文件
        fp = open(self.name, "wb")
        fp.truncate(self.size)
        fp.close()
        # 启动多线程写文件
        part = self.size // self.num
        pool = ThreadPoolExecutor(max_workers=self.num+1)
        futures = []
        fp = open(self.name,"wb")
        for i in range(self.num):
            start = part * i
            # 最后一块
            if i == self.num - 1:
                end = self.size
            else:
                end = start + part - 1
            futures.append(pool.submit(self.down, start, end, fp))
        futures.append(pool.submit(self.showPercent))
        wait(futures)
        print('\n%s 下载完成' % self.name)
#https://www.jianshu.com/p/f98b004763c4
def exit(code,message=""):
    print("服务器返回了%s %s"%(code,message))
    traceback.print_stack()
    sys.exit(code)

def checkIsVaildId(id):
    if re.fullmatch(r"\d+",id):
        return int(id)
    elif re.fullmatch(r"av\d+",id):
        return int(id[2:])
    elif re.fullmatch(r"BV1[fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF]{2}4[fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF]1[fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF]7[fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF]{2}",id):
        return dec(id)
    elif re.fullmatch(r"ep\d+",id) or re.fullmatch(r"ss\d+",id) or re.fullmatch(r"md\d+",id):
        return id
    else:
        return None

def getBangumi(id):
    if re.fullmatch(r"md\d+",id):
        id=requests.get("http://api.bilibili.com/pgc/review/user?media_id="+id[2:]).json()
        if id["code"]!=0:
            exit(id["code"],id["message"])
        id="ss"+str(id["result"]["media"]["season_id"])
    if re.fullmatch(r"ss\d+",id):
        link="http://api.bilibili.com/pgc/view/web/season?season_id="+id[2:]
    else:
        link="http://api.bilibili.com/pgc/view/web/season?ep_id="+id[2:]
    r=requests.get(link).json()
    if r["code"]:
        exit(r["code"],r["message"])
    global stream_URL
    stream_URL="https://api.bilibili.com/pgc/player/web/playurl?avid=%s&cid=%s"
    return {"data":{"title":r["result"]["title"],"pages":r["result"]["episodes"]}}


def removeChars(name):
	for i in r'\/:*?"<>|':
		name=name.replace(i,' ')
	return name

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.description="下载视频的工具，只支持av/bv/ss/ep/md号，by Minecraftku_hei"
    parser.add_argument("avid",help="av号或bv号")
    parser.add_argument("-r","--resolution",help="清晰度，16=360P 32=480P 64=720P 74=720P60FPS 80=1080P 112=1080P+ 116=1080P60FPS 120=4K，720P以上需要扫码登录",type=int)
    parser.add_argument("--start",help="开始的分P",type=int)
    parser.add_argument("--stop",help="结束的分P",type=int)
    parser.add_argument("--only",help="只下载某个分P",type=int)
    parser.add_argument("-t","--threads",help="多线程，最大1024线程",type=int)
    parser.add_argument("-m","--mode",help="模式:1.flv模式，存在限速，部分视频有分段 2.mp4模式，限速65k，只支持360/240p，无视频分段 3.dash模式，无限速，无视频分段，音视频分离。",type=int)
    parser.add_argument("-v","--videoOnly",action="store_true",help="只下载视频")
    parser.add_argument("-a","--audioOnly",action="store_true",help="只下载音频")
    parser.add_argument("-s","--sessdata",help="cookie里的SESSDATA，填入此项就不会要求扫码了")
    parser.add_argument("-c","--csrf",help="cookie里的bili_jct，如果显示-412请填入此项")
    parser.add_argument("-o","--to",help="输出文件")
    args=parser.parse_args()
    if not args.to:
    	args.to="."
    avid=checkIsVaildId(args.avid)
    if not avid:
        print("无效av/bv/ss/ep/md号")
        sys.exit(-1)
    cookies={}
    fourk=0
    resolution=args.resolution #16=360P 32=480P 64=720P 74=720P60FPS 80=1080P 112=1080P+ 116=1080P60FPS 120=4K
    if not resolution: resolution=32
    if resolution>=64 and not args.sessdata:
        print("二维码已生成，注意弹窗")
        cookies=login()
    if args.sessdata:
        cookies["SESSDATA"]=args.sessdata
    if args.csrf:
        cookies["bili_jct"]=args.csrf
    if resolution>=120:
        fourk=1
    if type(avid)==str:
        status=getBangumi(avid)
    else:
        status=requests.get(status_URL%(avid,),cookies=cookies).json()
        if status["code"]!=0:
            exit(status["code"],status["message"])
    i=0
    start=0
    if args.start:
        start=max(0,args.start-1)
    stop=len(status["data"]["pages"])
    if args.stop:
        stop=min(stop,args.stop)
    if args.only:
        start=max(0,args.only-1)
        stop=min(stop,args.only)
    for partid in range(start,stop):
        parts=status["data"]["pages"][partid]
        if parts.get("aid"):
            avid=parts["aid"]
        #print(stream_URL%(avid,parts["cid"])+"&qn=%s&fourk=%s&fnval=%s"%(resolution,fourk,16 if args.mode==3 else 1 if args.mode==2 else 0))
        stream=requests.get(stream_URL%(avid,parts["cid"])+"&qn=%s&fourk=%s&fnval=%s"%(resolution,fourk,16 if args.mode==3 else 1 if args.mode==2 else 0),cookies=cookies,headers={'referer':'https://www.bilibili.com/'})
        if stream.json()["code"]!=0: exit(stream.json()["code"],stream.json()["message"])
        if args.mode!=3:
            j=0
            for part in stream.json()["result" if "pgc" in stream_URL else "data"]["durl"]:
                j+=1
                filename=removeChars("%s%s(%s).%s"%(status["data"]["title"],partid+1,j,part['url'].split('/')[-1].split("?")[0].split('.')[-1]))
                print("\n开始下载"+filename)
                filename=os.path.join(args.to,filename)
                headers={}
                headers["Referer"]='https://www.bilibili.com/video/av%s'%(avid,)
                headers["Origin"]="https://www.bilibili.com"
                headers["User-Agent"]="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
                #threading.Thread(target=download,args=(f,part['url'],stream.cookies,headers),daemon=True).start()
                if not args.threads:
                    f=open(filename,'wb')
                    threads=0
                    download(f,part['url'],stream.cookies,headers)
                    f.close()
                else:
                    threads=args.threads
                    Downloader(part['url'],threads,filename,part["size"]).run()
        if args.mode==3:
            if not args.audioOnly:
                url=stream.json()["result" if "pgc" in stream_URL else 'data']['dash']['video'][0]['baseUrl']
                filename=removeChars("%s%s(%s).%s"%(status["data"]["title"],partid+1,0,'mp4'))
                print("\n开始下载"+filename)
                filename=os.path.join(args.to,filename)
                headers={}
                headers["Referer"]='https://www.bilibili.com/video/av%s'%(avid,)
                headers["Origin"]="https://www.bilibili.com"
                headers["User-Agent"]="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
                #threading.Thread(target=download,args=(f,part['url'],stream.cookies,headers),daemon=True).start()
                if not args.threads:
                    f=open(filename,'wb')
                    threads=0
                    download(f,url,stream.cookies,headers)
                    f.close()
                else:
                    threads=args.threads
                    Downloader(url,threads,filename).run()
            if not args.videoOnly:
                url=stream.json()["result" if "pgc" in stream_URL else 'data']['dash']['audio'][0]['baseUrl']
                filename=removeChars("%s%s(%s).%s"%(status["data"]["title"],partid+1,0,'aac'))
                print("\n开始下载"+filename)
                filename=os.path.join(args.to,filename)
                headers={}
                headers["Referer"]='https://www.bilibili.com/video/av%s'%(avid,)
                headers["Origin"]="https://www.bilibili.com"
                headers["User-Agent"]="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
                #threading.Thread(target=download,args=(f,part['url'],stream.cookies,headers),daemon=True).start()
                if not args.threads:
                    f=open(filename,'wb')
                    threads=0
                    download(f,url,stream.cookies,headers)
                    f.close()
                else:
                    threads=args.threads
                    Downloader(url,threads,filename).run()

