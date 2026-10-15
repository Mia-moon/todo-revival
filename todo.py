#编码方式：
 #终端输出utf-8,控制台输出为gbk,所以打印出来中文乱码，需要将控制台的也改为utf-8
import sys 
#sys ：系统相关标准库模块。偏 Python 解释器、运行时环境
#os：偏操作系统、文件、目录、进程等操作
import argparse #命令行参数解析模块
from pathlib import Path  #操作文件路径和目录
import json 
from datetime import datetime
import os #操作系统接口，提供 os.fdopen、os.replace、os.path.exists、os.unlink 等
import tempfile #专门创建临时文件和临时目录的模块。

if hasattr(sys.stdout,"reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

#默认定义文件路径变量
todo_file=Path("todo.json")
#读json文件内容
def load_todos():
    if not todo_file.exists():
        return []
    with open(todo_file,"r",encoding="utf-8") as f:
        #防止文件为空或损坏：增加conten变量获取文件内容
        content =f.read().strip()
        #如果文件内容不存在，返回[];否则try except判断内容格式，格式不对返回空
        if not content:
            return []
        try:
    #这里要用 json.loads(content) 而不是 json.load(f)
     #因为上文有 f.read() 已经把文件指针移到末尾。有f.read()就不能再用json.load()
          return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"文件损坏，原因：{e}")
            return []
#写入json内容（二编：防止数据中途写入失败，增加临时文件最后替换）
def save_todos(todos):
 #初编：
   # with open(todo_file,"w",encoding="utf-8") as f:
      #  json.dump(todos,f,ensure_ascii=False,indent=2)
 #二编：
    #先创建临时文件：mkstemp()创建文件 mkdtemp()创建目录
     #fd 文件描述符，tmp临时文件的路径字符串,
     #dir="." 临时文件放在当前目录，必须和todo_file同目录，os.replace才能原子替换
     #profix=".todo-" 文件名前缀，以点开头在linux下是隐藏文件；suffix=".tmp"文件名后缀，表临时文件
    fd,tmp=tempfile.mkstemp(dir=".",prefix=".todo-",suffix=".tmp")
    #向临时文件写入,文件描述符只能用os.fdopen()方法包装成文件对象.try except出错时清理临时文件
    try:
     with os.fdopen(fd,"w",encoding="utf-8") as f:
        json.dump(todos,f,ensure_ascii=False,indent=2)
    #路径替换
     os.replace(tmp,todo_file)
    except:
        if os.path.exists(fd):
            os.unlinkI(tmp) #删除临时文件
        raise #raise后不加内容，会直接抛出当前异常   

#add方法添加并保存
def add_todo(text):
    todos=load_todos()
    new_id=max([todic["id"] for todic in todos ],default=0)+1
    #datetime.now() 获取当前本地日期和时间 .isoformat() 把日期时间对象转换成iso 8601格式字符串
    # (timespec="seconds") 指定精确到秒，不显示微秒
    todos.append({
        "id":new_id,
        "text":text,
        "done":False,
        "createtime":datetime.now().isoformat(timespec="seconds"),
        "done_at":None,
    })
    save_todos(todos)
    print(f"已添加 #{new_id}:{text}")

#list方法列出部分/全部
def list_todo(show_all=False):
    todos=load_todos()
    for t in todos:
        if not show_all and t["done"]: #如果不显示全部且已完成则跳过不打印。
            continue #跳过本次，直接执行下一次
        #status= 三元表达式
        status=green("[√]") if t["done"] else red("[]") 
        print(f"{status} 代办编号：{t['id']} 代办内容：{t['text']} 状态：{t['done']} 创建时间：{t['createtime']} 完成时间：{t['done_at']}")

#done方法标志完成项
def done_todo(ids):
    todos=load_todos()
    for tid in ids:
        for t in todos:
            if t["id"]==tid:
                t["done"]=True
                t["done_at"]=datetime.now().isoformat(timespec="seconds")
                print(f"已完成{t['id']} {t['text']}")
                break
        else:
            print(f"找不到{tid}")
    save_todos(todos)

#del删除不要的项
def del_todo(ids):
    todos=load_todos()
    new_todos=[t for t in todos if t['id'] not in ids]
    removed=len(todos)-len(new_todos)
    save_todos(new_todos)
    if len(ids)!=removed:
        print("存在未知编号，请输入代办已有编号")
    print(f"已删除{removed}项")

#构建解析器parser，可以职责分离（build_parser()只定义参数规则，main()只负责业务逻辑）
def build_parser():
    #prog为程序名
    parser=argparse.ArgumentParser(prog="todo",description="命令行代办工具")
    parser.add_argument("-f","--file",help="数据文件路径") #-f参数加到主解析器，即为全局参数。放在子命令前。
    sub=parser.add_subparsers(dest="command",required=True,metavar="命令")

    #add 参数为text
    p_add=sub.add_parser("add",help="添加代办")
    p_add.add_argument("text",nargs="+",help="代办内容") #nargs="+"：至少一个内容

    #list 参数为-a --all
    p_list=sub.add_parser("list",help="显示代办")
    p_list.add_argument("-a","--all",action="store_true",help="显示全部")
    #action="store_true" 是 argparse 中用来定义一个布尔开关（flag） 的标准方式。让参数变成布尔类型。
    #它表示这个参数是一个“开关”，用户带上它，值就是 True；不带，值就是 False。

    #done 参数为ids
    p_done=sub.add_parser("done",help="完成代办")
    p_done.add_argument("ids",nargs="+",type=int,help="代办编号")

    #del 参数为ids
    p_del=sub.add_parser("del",help="删除代办")
    p_del.add_argument("ids",nargs="+",type=int,help="代办编号")

    #文件路径 -f参数修改文件路径
    #p_file=sub.add_parser("file",help="文件路径")
    #p_file.add_argument("-f","--file",default="todo.json",help="数据文件路径")

    #返回配置好的解析器，交给调用者
    return parser

#配置颜色
 #\033[ == ESC[:控制序列开始,后面为控制指令传给终端；32 ：颜色代码，绿色；m ：设置图形属性（颜色，加粗、下划线等）。
 #\033[ ：控制序列开始; 0:重置所有属性 ; m:设置图形属性。\033[0m作用：把颜色恢复成默认值，防止后面的也是绿色。
def green(s): return f"\033[32m{s}\033[0m"
def red(s) : return f"\033[31m{s}\033[0m"
def gray(s): return f"\033[90m{s}\033[0m"

#定义文件路径可修改
def get_todo_file(args):
    if args.file: #如果命令行输入-f参数，则走这里，返回-f 指定的文件
        return Path(args.file)
    if os.environ.get("todo_file"): #如果用环境变量走这里
        return Path(os.environ["todo_file"])
    return Path("todo.json") #都没有指定走todo.json

# 定义函数main()，存放主要逻辑
def main():
    #因为python允许不同函数存在相同变量名称。这里需要赋值，因此global声明表示操作的是全局变量，而非又新建的局部变量.
    #如果只是读取，则不用global声明，函数查不到局部会去全局变量查询。
   global todo_file
   parser=build_parser()  #构造解析器，定义规则
   args=parser.parse_args() #识别命令行，获取命令行的数据
   todo_file=get_todo_file(args) #文件指向用户又更改的
   

   if args.command=="add":
       text=" ".join(args.text).strip()
       if not text:
           print("内容不能为空")
           return
       add_todo(text)

   elif args.command=="list":
       list_todo(show_all=args.all)

   elif args.command=="done":
       done_todo(args.ids)

   elif args.command=="del":
       del_todo(args.ids)


#name=main 判断，只有直接运行该文件时，才执行main(),
 # 如果该文件被其他import，就不自动执行，需要调用执行。
if __name__=="__main__":
    main()
