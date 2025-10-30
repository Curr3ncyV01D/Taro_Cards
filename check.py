# check_media.py
import os


def check_media_files():
    media_dir = "media"
    required_files = [
        'shut.gif', 'mag.gif', 'zhrica.gif', 'impress.gif', 'imperor.gif',
        'hierofant.gif', 'lovers.gif', 'chariot.gif', 'strengch.gif', 'hermit.gif',
        'fortune.gif', 'justice.gif', 'hanged_man.gif', 'death.gif', 'temperam.gif',
        'devil.gif', 'tower.gif', 'stare.gif', 'moon.gif', 'sun.gif', 'sud.gif', 'world.gif'
    ]

    print("Проверка медиафайлов...")
    for filename in required_files:
        file_path = os.path.join(media_dir, filename)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {filename} - {size} bytes")
        else:
            print(f"❌ {filename} - НЕ НАЙДЕН")

    # Проверяем существование папки media
    if not os.path.exists(media_dir):
        print(f"❌ Папка '{media_dir}' не существует!")
        print("Создайте папку 'media' и поместите туда все GIF файлы")


if __name__ == "__main__":
    check_media_files()