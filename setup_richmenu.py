from linebot import LineBotApi
from linebot.models import RichMenu, RichMenuArea, RichMenuBounds, MessageAction
import json

CHANNEL_ACCESS_TOKEN = "RgdlVa2/M981fASPei1fz+p8VxMMltZDC3MyZKrfqiHo59UsZye5LmSJx2v7wc8+DT4VxlnVL9RSOlpTQRtFDfj8IIt6jgBLyjj/E/EuepWi3ymkVRg44h72q3NcTGje3vTDHKzPuWYNnrd8OVx1JAdB04t89/1O/w1cDnyilFU="
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)

def create_rich_menu():
    # สร้าง Rich Menu
    rich_menu = RichMenu(
        size={"width": 2500, "height": 843},  # ขนาดมาตรฐาน
        selected=True,
        name="COAI Rich Menu",
        chat_bar_text="เมนูหลัก",
        areas=[
            RichMenuArea(
                bounds=RichMenuBounds(x=0, y=0, width=2500, height=843),
                action=MessageAction(label="เช็คห้อง CO", text="เช็คห้อง CO")
            )
        ]
    )

    # สร้าง Rich Menu ใน LINE
    rich_menu_id = line_bot_api.create_rich_menu(rich_menu=rich_menu)
    print(f"✅ Created Rich Menu: {rich_menu_id}")

    # ใส่รูปปุ่ม
    with open("button.png", "rb") as f:  # ต้องมีไฟล์ button.png อยู่ในโฟลเดอร์เดียวกัน
        line_bot_api.set_rich_menu_image(rich_menu_id, "image/png", f)

    # ตั้งค่า Rich Menu ให้เป็นค่าเริ่มต้น
    line_bot_api.set_default_rich_menu(rich_menu_id)
    print("✅ Set Rich Menu as default.")

if __name__ == "__main__":
    create_rich_menu()