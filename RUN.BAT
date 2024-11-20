@echo off
REM 进入脚本所在的目录
cd %~dp0

REM 设置命令行编码为 UTF-8，避免解码错误
chcp 65001

REM 激活虚拟环境（如果还没有创建虚拟环境，则先创建一个）
if not exist venv (
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate

REM 升级 pip，避免升级时的编码问题
python -m pip install --upgrade pip

REM 安装依赖库
pip install -r requirements.txt

REM 运行 Python 脚本
python main.py

REM 保持窗口打开
echo.
echo 处理完成！按任意键退出...
pause
