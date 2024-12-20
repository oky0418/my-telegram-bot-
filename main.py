import logging
import random
import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# 日志设置
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# 管理员列表
ADMINS = [123456789, 987654321]  # 示例管理员 ID
ADMIN_USERNAMES = ["xianyuge_2014"]  # 管理员的用户名列表

# 数据存储（模拟数据库）
users = {}
red_packets = []
daily_signin_reward = 100

def get_user_data(user_id):
    """初始化或获取用户数据"""
    if user_id not in users:
        users[user_id] = {
            "balance": 0,
            "last_signin": None
        }
    return users[user_id]

def is_admin(user_id, username=None):
    """检查用户是否为管理员"""
    return user_id in ADMINS or (username in ADMIN_USERNAMES if username else False)

# /start 命令
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    get_user_data(user.id)
    await update.message.reply_text(f"欢迎使用娱乐机器人，{user.first_name}！输入 /help 查看所有可用命令。")

# 查看指令功能
async def help_command(update: Update, context: CallbackContext):
    commands = """
以下是可用指令列表：

💰 用户功能：
/signin - 每日签到，获取奖励
/wallet - 查看当前余额
/myid - 查看你的用户 ID
/deposit <金额> - 存款金币
/withdraw <金额> - 提取金币
/transfer <用户ID> <金额> - 向其他用户转账
/redpacket <总金额> <数量> - 发红包
/grab - 抢红包

🎲 娱乐游戏：
/dragon_tiger <下注金额> <龙/虎> - 参与龙虎斗游戏，选择龙或虎下注，系统会随机决定胜负

❓ 帮助：
/help - 查看指令列表
"""
    await update.message.reply_text(commands)

# 签到功能
async def signin(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)

    today = datetime.date.today()
    if user_data["last_signin"] == today:
        await update.message.reply_text("今天已经签到过了！")
    else:
        user_data["balance"] += daily_signin_reward
        user_data["last_signin"] = today
        await update.message.reply_text(f"签到成功！获得 {daily_signin_reward} 金币。当前余额：{user_data['balance']}")

# 查看钱包
async def wallet(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    if is_admin(user_id, update.effective_user.username):
        await update.message.reply_text("你是管理员，拥有无限金币权限！")
    else:
        await update.message.reply_text(f"你的余额为：{user_data['balance']} 金币")

# 查看用户 ID
async def myid(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    await update.message.reply_text(f"你的用户 ID 是：{user_id}")

# 存款
async def deposit(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)

    try:
        amount = int(context.args[0])
        if amount <= 0:
            raise ValueError
    except (IndexError, ValueError):
        await update.message.reply_text("请输入正确的存款金额，例如：/deposit 100")
        return

    user_data["balance"] += amount
    await update.message.reply_text(f"成功存款 {amount} 金币！当前余额：{user_data['balance']}")

# 提款
async def withdraw(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)

    try:
        amount = int(context.args[0])
        if amount <= 0:
            raise ValueError
    except (IndexError, ValueError):
        await update.message.reply_text("请输入正确的提款金额，例如：/withdraw 50")
        return

    if is_admin(user_id, update.effective_user.username):
        await update.message.reply_text(f"成功提款 {amount} 金币！（管理员无限金币权限）")
    elif user_data["balance"] < amount:
        await update.message.reply_text("余额不足！")
    else:
        user_data["balance"] -= amount
        await update.message.reply_text(f"成功提款 {amount} 金币！当前余额：{user_data['balance']}")

# 转账
async def transfer(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)

    try:
        target_user_id = int(context.args[0])
        amount = int(context.args[1])
        if amount <= 0:
            raise ValueError
    except (IndexError, ValueError):
        await update.message.reply_text("请输入正确的格式，例如：/transfer <用户ID> <金额>")
        return

    target_user_data = get_user_data(target_user_id)

    if is_admin(user_id, update.effective_user.username):
        target_user_data["balance"] += amount
        await update.message.reply_text(f"管理员成功向用户 {target_user_id} 转账 {amount} 金币！")
    elif user_data["balance"] < amount:
        await update.message.reply_text("余额不足！")
    else:
        user_data["balance"] -= amount
        target_user_data["balance"] += amount
        await update.message.reply_text(f"成功向用户 {target_user_id} 转账 {amount} 金币！")

# 发红包
async def redpacket(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)

    try:
        total_amount = int(context.args[0])  # 红包总金额
        num_packets = int(context.args[1])  # 红包数量
        if total_amount <= 0 or num_packets <= 0 or num_packets > total_amount:
            raise ValueError
    except (IndexError, ValueError):
        await update.message.reply_text("请输入正确的格式，例如：/redpacket 100 5（总金额为100，共5个红包）")
        return

    if not is_admin(user_id, update.effective_user.username) and user_data["balance"] < total_amount:
        await update.message.reply_text("余额不足，无法发红包！")
        return

    # 扣除金额
    if not is_admin(user_id, update.effective_user.username):
        user_data["balance"] -= total_amount

    # 随机生成红包金额
    packets = []
    for _ in range(num_packets - 1):
        amount = random.randint(1, total_amount - len(packets) - (num_packets - len(packets)) + 1)
        packets.append(amount)
        total_amount -= amount
    packets.append(total_amount)

    # 保存红包信息
    red_packets.extend(packets)
    await update.message.reply_text(f"红包已发出，共 {num_packets} 个红包！使用 /grab 抢红包！")

# 抢红包
async def grab(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)

    if not red_packets:
        await update.message.reply_text("当前没有可抢的红包！")
        return

    # 抢红包
    amount = red_packets.pop(0)
    user_data["balance"] += amount
    await update.message.reply_text(f"恭喜抢到 {amount} 金币！当前余额：{user_data['balance']}")

# 龙虎斗游戏
async def dragon_tiger(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)

    # 检查是否有下注金额
    try:
        bet_amount = int(context.args[0])
        if bet_amount <= 0:
            raise ValueError
    except (IndexError, ValueError):
        await update.message.reply_text("请输入有效的下注金额，例如：/dragon_tiger 50")
        return

    if user_data["balance"] < bet_amount:
        await update.message.reply_text("余额不足，无法下注！")
        return

    # 让玩家选择“龙”或“虎”
    choice = context.args[1].lower() if len(context.args) > 1 else None
    if choice not in ["龙", "虎"]:
        await update.message.reply_text("请选择有效的选项：/dragon_tiger <下注金额> <龙/虎>")
        return

    # 生成龙和虎的点数
    dragon = random.randint(1, 6)
    tiger = random.randint(1, 6)

    # 计算胜负
    if dragon > tiger:
        winner = "龙"
    elif tiger > dragon:
        winner = "虎"
    else:
        winner = "和"

    # 比较玩家的选择与实际结果
    if winner == choice:
        user_data["balance"] += bet_amount
        await update.message.reply_text(f"恭喜！你选择了{choice}，获胜！\n龙: {dragon} - 虎: {tiger}\n你赢得了 {bet_amount} 金币！当前余额：{user_data['balance']}")
    elif winner == "和":
        await update.message.reply_text(f"平局！\n龙: {dragon} - 虎: {tiger}\n没有输赢。")
    else:
        user_data["balance"] -= bet_amount
        await update.message.reply_text(f"很遗憾，你选择了{choice}，但是这局胜利的是{winner}。\n龙: {dragon} - 虎: {tiger}\n你输了 {bet_amount} 金币。当前余额：{user_data['balance']}")

# 管理员调整用户余额
async def admin_adjust(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id

    # 检查是否是管理员
    if not is_admin(user_id, user.username):
        await update.message.reply_text("您无权使用此命令！")
        return

    try:
        target_user_id = int(context.args[0])  # 目标用户 ID
        amount = int(context.args[1])  # 调整的金额
    except (IndexError, ValueError):
        await update.message.reply_text("使用格式：/admin_adjust <用户ID> <金额>\n例如：/admin_adjust 123456789 500")
        return

    # 初始化或获取目标用户数据
    target_user_data = get_user_data(target_user_id)

    # 调整目标用户余额
    target_user_data["balance"] += amount

    await update.message.reply_text(
        f"成功调整用户 {target_user_id} 的余额！\n"
        f"调整金额：{amount}\n当前余额：{target_user_data['balance']}"
    )

# 查看管理员无限金币权限
async def admin_wallet(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if is_admin(user_id, update.effective_user.username):
        await update.message.reply_text("你是管理员，拥有无限金币权限！")
    else:
        await update.message.reply_text("你不是管理员，没有此权限！")

# 主函数，使用 asyncio 运行异步方法
async def main():
    # 替换为你的实际 API 密钥
    application = Application.builder().token("8064239780:AAGWmFo9PhJmhX57trg4JwNUltBjMt8uSsM").build()

    # 注册命令处理
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("signin", signin))
    application.add_handler(CommandHandler("wallet", wallet))
    application.add_handler(CommandHandler("myid", myid))
    application.add_handler(CommandHandler("deposit", deposit))
    application.add_handler(CommandHandler("withdraw", withdraw))
    application.add_handler(CommandHandler("transfer",
application.add_handler(CommandHandler("transfer", transfer))
    application.add_handler(CommandHandler("redpacket", redpacket))
    application.add_handler(CommandHandler("grab", grab))
    application.add_handler(CommandHandler("dragon_tiger", dragon_tiger))
    application.add_handler(CommandHandler("admin_adjust", admin_adjust))
    application.add_handler(CommandHandler("admin_wallet", admin_wallet))

    # 启动 bot
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())